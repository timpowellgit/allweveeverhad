from skimage.feature import hog
from skimage import data, exposure
import os
from skimage.io import imread
import pandas as pd
from skimage.transform import resize
import random
import scipy
from scipy import spatial
from tqdm import tqdm
import tempfile
import subprocess
from PIL import Image
from multiprocessing import Pool
import skimage
from skimage.io import imread
from skimage import measure
from skimage.color import rgb2gray
import numpy as np
from skimage import measure, feature, io, color, draw, transform

DEBUG_MAX_IMGS = 1000

IMG_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-images'

img_paths = filter(lambda _: _.endswith('.jpg'), os.listdir(IMG_DIR))

descriptor_values = []

def get_moments_vector(file_path):
  full_path = os.path.join(IMG_DIR, file_path)
  im = skimage.io.imread(full_path)
  im = rgb2gray(im)
  mu = measure.moments_central(im)
  nu = measure.moments_normalized(mu)
  hu = measure.moments_hu(nu)
  return [hu]

def get_ransac_vector(file_path):
  file_path = os.path.join(IMG_DIR, file_path)
  img = color.rgb2gray(io.imread(file_path))
  img = transform.resize(img, (512, 512))

  img = feature.canny(img).astype(np.uint8)
  img[img > 0] = 255

  coords = np.column_stack(np.nonzero(img))

  circle_model, inliers = measure.ransac(coords, measure.CircleModel, 20, 3)

  line_model, inliers = measure.ransac(coords, measure.LineModelND, 20, 3)
  line_model = [__ for _ in line_model.params for __ in _]

  return [list(circle_model.params) + list(line_model)]


print 'starting pool'
p = Pool(7)
descriptor_values = zip(img_paths[:DEBUG_MAX_IMGS], map(get_ransac_vector, tqdm(img_paths[:DEBUG_MAX_IMGS])))
print('descriptor_values', descriptor_values)
descriptor_values = filter(lambda _: _[1] is not None, descriptor_values)
print 'vector len', len(descriptor_values[0][1][0])

filenames, values = zip(*descriptor_values)

descriptors_pandas = pd.DataFrame(list(values), index=filenames, columns=['fd'])


needle_filepath = random.choice(img_paths[:DEBUG_MAX_IMGS])
needle_vector = filter(lambda _:_[0] == needle_filepath, descriptor_values)[0][1][0]
print('needle_vector', needle_vector)

dist = scipy.spatial.distance.cdist(descriptors_pandas['fd'].tolist(), [needle_vector])
dist_pandas = pd.DataFrame(dist, index=filenames, columns=['dist'])
dist_pandas_sorted = dist_pandas.sort_values('dist')

print 'dist_pandas_sorted'
print dist_pandas_sorted
