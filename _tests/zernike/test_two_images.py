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
from mahotas.features import zernike_moments
import numpy as np
import mahotas
import mahotas
from mahotas.features import zernike_moments
import numpy as np
import skimage
from skimage import measure, feature, io, color, draw, transform
from skimage.color import rgb2gray
import sys
import os

def get_zernike_vector(file_path):
  im = skimage.io.imread(file_path)
  im = rgb2gray(im)
  im = mahotas.imresize(im, (256,256))

  vector = zernike_moments(im, radius=256, degree=20)
  return vector

if __name__ == '__main__':
  v1 = get_zernike_vector(sys.argv[1])
  v2 = get_zernike_vector(sys.argv[2])
  print('v1', v1)
  print('v2', v2)
  print 'distance',scipy.spatial.distance.cdist([v1], [v2])
