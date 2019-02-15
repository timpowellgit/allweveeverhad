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
from skimage.transform import resize
import sklearn
from sklearn.decomposition import RandomizedPCA, PCA
import os
from skimage.transform import resize
import imagehash

DEBUG_MAX_IMGS = 1000

IMG_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-images'

img_paths = filter(lambda _: _.endswith('.jpg'), os.listdir(IMG_DIR))

descriptor_values = []

def get_phash_vector(file_path):
  full_path = os.path.join(IMG_DIR, file_path)
  return [imagehash.phash(Image.open(full_path)).hash.flatten().astype(int)]

print 'starting pool'
p = Pool(7)
descriptor_values = zip(img_paths[:DEBUG_MAX_IMGS], map(get_phash_vector, tqdm(img_paths[:DEBUG_MAX_IMGS])))
descriptor_values = filter(lambda _: _[1] is not None, descriptor_values)
print 'vector len', len(descriptor_values[0][1][0])

filenames, values = zip(*descriptor_values)
descriptors_pandas = pd.DataFrame(list(values), index=filenames, columns=['fd'])

needle_filepath = "afv2nKV0HAzCagIM0Hecgw.jpg"
needle_vector = filter(lambda _:_[0] == needle_filepath, descriptor_values)[0][1][0]
needle_filepath2 = "afv2nKV0HAzCagIM0Hecgw-1.jpg"
needle_vector2 = filter(lambda _:_[0] == needle_filepath2, descriptor_values)[0][1][0]
needle_filepath3 = "afv2nKV0HAzCagIM0Hecgw-2.jpg"
needle_vector3 = filter(lambda _:_[0] == needle_filepath3, descriptor_values)[0][1][0]

dist = scipy.spatial.distance.cdist(descriptors_pandas['fd'].tolist(), [needle_vector, needle_vector2, needle_vector3])
dist_pandas = pd.DataFrame(dist, index=filenames, columns=['d1','d2','d3'])
dist_pandas_sorted = dist_pandas.sort_values('d1')

print 'dist_pandas_sorted'
print dist_pandas_sorted
