from itertools import chain
from lshash import LSHash
from multiprocessing import Pool
from PIL import Image
from scipy import spatial
from skimage import data, exposure
from skimage import measure
from skimage import measure, feature, io, color, draw, transform
from skimage.color import rgb2gray
from skimage.feature import hog
from skimage.io import imread
from skimage.transform import resize
from tqdm import tqdm
import imageio
import numpy as np
import operator
import os
import pandas as pd
import pickle
import random
import scipy
import skimage
import subprocess
import sys
import tempfile

NMB_BINS = 16
HIST_USE_DENSITY = True


DEBUG_MAX_IMGS = 1000

IMG_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/allpainters-scraping/img'

img_paths = filter(lambda _: _.endswith('.jpg'), os.listdir(IMG_DIR))

descriptor_values = []

def generate_hist(im):
  nmb_channels = None
  if len(im.shape) == 3 and im.shape[2] == 3:
    nmb_channels = 3
  elif len(im.shape) == 2:
    nmb_channels = 1
  if nmb_channels is None:
    print 'ERR not 1 or 3 chans',im.shape
    return None

  # make sure that we're dealing with 3 channel images only
  im = im.reshape(im.shape[0] * im.shape[1], nmb_channels)

  c_histograms = [np.histogram(im[:,_], bins=NMB_BINS,
                                  density=HIST_USE_DENSITY, range=(0,255))[0] \
                                                  for _ in range(nmb_channels)]

  if nmb_channels == 1:
    # propagate single channel histogram values into rgb channels
    c_histograms = c_histograms * 3

  return np.array(list(chain.from_iterable(c_histograms)))

def get_sub_rect(img, x0, y0, width, height):
  return np.copy(img[y0:y0 + height, x0:x0 + width])

def get_multi_hist_vector(file_path):
  file_path = os.path.join(IMG_DIR, file_path)
  im = imageio.imread(file_path)
  h, w = im.shape[:2]
  x_delta = w/3
  y_delta = h/3
  muli_hist_vect = []
  for x_idx in range(3):
    for y_idx in range(3):
      sub_img = get_sub_rect(im, x0=x_idx*x_delta, y0=y_idx*y_delta, width=x_delta, height=y_delta)
      hist_vector = generate_hist(sub_img)
      muli_hist_vect.append(hist_vector)
  img_multi_hist_vect = np.array(list(chain.from_iterable(muli_hist_vect)))
  return [img_multi_hist_vect]

def get_hist_vector(file_path):
  file_path = os.path.join(IMG_DIR, file_path)
  im = imageio.imread(file_path)
  hist_vector = generate_hist(im)
  return [np.array(list(chain.from_iterable([hist_vector])))]

# FIXME switch back to get_multi_hist_vector as necessary......!!
# FIXME switch back to get_multi_hist_vector as necessary......!!
# FIXME switch back to get_multi_hist_vector as necessary......!!
# FIXME switch back to get_multi_hist_vector as necessary......!!
descriptor_values = zip(img_paths[:DEBUG_MAX_IMGS], map(get_multi_hist_vector, tqdm(img_paths[:DEBUG_MAX_IMGS])))
descriptor_values = filter(lambda _: _[1] is not None, descriptor_values)
print 'vector len', len(descriptor_values[0][1][0])

filenames, values = zip(*descriptor_values)

descriptors_pandas = pd.DataFrame(list(values), index=filenames, columns=['fd'])


# needle_filepath = random.choice(img_paths[:DEBUG_MAX_IMGS])
needle_filepath = "img482-180.jpg"
needle_vector = filter(lambda _:_[0] == needle_filepath, descriptor_values)[0][1][0]

dist = scipy.spatial.distance.cdist(descriptors_pandas['fd'].tolist(), [needle_vector])
dist_pandas = pd.DataFrame(dist, index=filenames, columns=['d1'])
dist_pandas_sorted = dist_pandas.sort_values('d1')

print 'dist_pandas_sorted'
print dist_pandas_sorted

