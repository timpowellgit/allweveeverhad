from collections import defaultdict
from matplotlib import cm
from multiprocessing import Pool
from PIL import Image
from scipy import spatial
from skimage import color, data, exposure, filters, measure, feature, io, color, draw, transform
from skimage.color import rgb2gray, rgb2grey
from skimage.draw import line
from skimage.exposure import equalize_adapthist
from skimage.feature import canny
from skimage.feature import hog
from skimage.io import imread, imsave
from skimage.transform import hough_line, hough_line_peaks, probabilistic_hough_line
from skimage.transform import resize
from sklearn.decomposition import RandomizedPCA, PCA
from tqdm import tqdm
import math
import matplotlib.pyplot as plt
import numpy as np
import operator
import os
import pandas as pd
import random
import scipy
import skimage
import sklearn
import subprocess
import tempfile

DEBUG_MAX_IMGS = 1000

DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/allpainters-scraping/img'

img_paths = filter(lambda _: _.endswith('.jpg'), os.listdir(DIR))

descriptor_values = []

def remove_margin(img,margin):
  y,x = img.shape
  return img[margin:margin+(y-margin*2),margin:margin+(x-margin*2)]

def get_hough_vector(filepath):
  img = imread(os.path.join(DIR, filepath))

  img = resize(img, (512,512))

  if len(img.shape) == 2:
    img = np.dstack((img, img, img))

  img_hsv = color.rgb2hsv(img)

  # extract s channel
  img_s = img_hsv[..., 1]

  img_equalized = equalize_adapthist(img_s)

  thres_sauvola_value = filters.threshold_sauvola(img_equalized)
  img_binarized = img_equalized <= thres_sauvola_value

  image = img_binarized

  image = remove_margin(image, 20)

  # Classic straight-line Hough transform
  h, theta, d = hough_line(image)

  h, angle, dist = hough_line_peaks(h, theta, d)
  results = zip(h, angle, dist)
  # only keep top 10 results
  results = results[:10]
  # abs angles
  results = filter(lambda (h,angle,dist): (abs(angle) < 0.1) or (abs(angle) > 1.4), results)
  # hough """score""" is (empirically) """high""" enough 
  results = filter(lambda (h,angle,dist): h > 350, results)

  all_angles = map(operator.itemgetter(1), results)
  # turn all angles absolute
  # this doesn't work for 45 degree angles (which we don't care about)
  # but does 'fold' horiz (near 0) and vertical (near 90 and -90) lines degrees together
  all_angles = map(abs, all_angles)
  angle_hist = np.histogram(all_angles, range=(0,math.pi/2), density=False)[0]

  vert_results = []
  horiz_results = []
  for h,angle,dist in results:
    # do the abs!!!!!!!!!!!!!!!!
    if abs(angle) < math.pi/4:
      vert_results.append((h,angle,dist))
    else:
      horiz_results.append((h,angle,dist))

  # distances are in range -diag,diag
  max_dist = math.sqrt(image.shape[0]**2 + image.shape[1]**2)

  # normalize distances according to diag
  # same as with angles, fold hough dist dimension upon itself......
  all_horiz_dist = map(lambda _: abs(_[2]/max_dist), horiz_results)
  all_vert_dist = map(lambda _: abs(_[2]/max_dist), vert_results)

  horiz_dist_hist = np.histogram(all_horiz_dist, range=(0,1), density=False)[0]

  vert_dist_hist = np.histogram(all_vert_dist, range=(0,1), density=False)[0]

  out = np.array([angle_hist, horiz_dist_hist, vert_dist_hist]).flatten()
  out[np.isnan(out)] = 1000 # very big value that will not match with '0' which is a separate, valid value
  return [out]


descriptor_values = zip(img_paths[:DEBUG_MAX_IMGS], map(get_hough_vector, tqdm(img_paths[:DEBUG_MAX_IMGS])))
descriptor_values = filter(lambda _: _[1] is not None, descriptor_values)
print 'vector len', len(descriptor_values[0][1][0])

filenames, values = zip(*descriptor_values)
descriptors_pandas = pd.DataFrame(list(values), index=filenames, columns=['fd'])

needle_filepath = 'img049.jpg'
needle_vector = filter(lambda _:_[0] == needle_filepath, descriptor_values)[0][1][0]

dist = scipy.spatial.distance.cdist(descriptors_pandas['fd'].tolist(), [needle_vector])
dist_pandas = pd.DataFrame(dist, index=filenames, columns=['d'])
dist_pandas_sorted = dist_pandas.sort_values('d')

print 'dist_pandas_sorted'
print dist_pandas_sorted
