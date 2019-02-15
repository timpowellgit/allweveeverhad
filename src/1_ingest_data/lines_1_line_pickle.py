from models import db, Artwork, Image
from tqdm import tqdm
import pickle
import os
from get_image_size import get_image_metadata
from collections import defaultdict
from matplotlib import cm
from multiprocessing import Pool
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
import sys

DEBUG = True

if DEBUG:
  ARTWORKS_SQLITE_PATH = "/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3"
  OUTPUT_LINE_PICKLE_PATH = "/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/hough_lines.lines.pickle"
else:
  if len(sys.argv) != 4:
    print 'ERR usage: python {} output_file start_idx end_idx'.format(sys.argv[0])
    exit()
  ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']
  #OUTPUT_LINE_PICKLE_PATH = os.environ['OUTPUT_LINE_PICKLE_PATH']
  OUTPUT_LINE_PICKLE_PATH = sys.argv[1]

db.init(ARTWORKS_SQLITE_PATH)

all_db_image_ids_paths = Image.select(Image.id, Image.img_local_path).tuples()

if DEBUG:
  DIR = '/Users/greg/Desktop/hough-test-imgs/doesnotworkonserver'
  all_db_image_ids_paths = [(idx, os.path.join(DIR, _)) for idx, _ in enumerate(os.listdir(DIR)) if os.path.isfile(os.path.join(DIR, _))]

# do hough line transform on "inside" of image so as not to match iamge's natural sides/frame
def remove_margin(img,margin):
  y,x = img.shape
  return img[margin:margin+(y-margin*2),margin:margin+(x-margin*2)]

def get_hough_line_vectors(filepath):
  img = imread(filepath)

  img = resize(img, (512,512))

  print('img.shape', img.shape)
  if len(img.shape) == 2:
    print 'stacking'
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

  # very big value that will not match with '0' which is a separate, valid value
  angle_hist[np.isnan(angle_hist)] = 1000
  horiz_dist_hist[np.isnan(horiz_dist_hist)] = 1000
  vert_dist_hist[np.isnan(vert_dist_hist)] = 1000

  return {
    'angle_hist': angle_hist,
    'horiz_dist_hist': horiz_dist_hist,
    'vert_dist_hist': vert_dist_hist
  }

with open(OUTPUT_LINE_PICKLE_PATH, 'a') as f:
  for image_id, image_path in tqdm(all_db_image_ids_paths[int(sys.argv[2]):int(sys.argv[3])]):
    if not image_path:
      continue
    try:
      img_line_vectors = get_hough_line_vectors(image_path)
    except Exception as e:
      print image_path
      print 'ERR calling get_hough_line_vectors', e
      continue

    pickle.dump((image_id, img_line_vectors), f)
