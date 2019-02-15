from skimage.transform import hough_line, hough_line_peaks, resize
from skimage.draw import line
import numpy as np
import os
import skimage
from skimage.io import imread
from skimage.color import rgb2grey

DIR = '/Users/greg/Desktop/hough-test-imgs/scans'
filepaths = filter(lambda _:_.endswith('.jpg'), os.listdir(DIR))
for filepath in filepaths:
  print('filepath', filepath)
  img = imread(os.path.join(DIR, filepath))
  img = resize(img, (512, 512))
  img = rgb2grey(img)
  img_bool = (img > 0.5)
  hspace, angles, dists = hough_line(img_bool)
  hspace, angles, dists = hough_line_peaks(hspace, angles, dists)
  print('hspace[:5]', hspace[:5])
  print('angles[:5]', angles[:5])
  print('dists[:5]', dists[:5])
  print len(angles)
