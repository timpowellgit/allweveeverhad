import os
import numpy as np
from skimage.io import imread
from math import pi, sin, cos
from skimage.io import imsave
# print full array
np.set_printoptions(threshold=np.nan)

IMG_DIR_PATH = '/Users/greg/Desktop/hough-test-imgs'

def build_hough_space_fom_image(img, shape=(200, 600), val=100):
  hough_space = np.zeros(shape)
  for i, row in enumerate(img):
    for j, pixel in enumerate(row):   
      if pixel != val:
        continue
      hough_space = add_to_hough_space_polar((i,j), hough_space)
  return hough_space

def add_to_hough_space_polar(p, feature_space):
  space = np.linspace(0, pi, len(feature_space))
  d_max = len(feature_space[0]) / 2
  for i in range(len(space)):
    theta = space[i]
    d = int(p[0] * sin(theta) + p[1] * cos(theta)) + d_max
    if (d >= d_max * 2) : continue
    feature_space[i, d] += 1
  return feature_space

if __name__ == '__main__':
  filepaths = filter(lambda _: _.endswith('.png') and 'hough' not in _, os.listdir(IMG_DIR_PATH))
  for filepath in filepaths:
    img = imread(os.path.join(IMG_DIR_PATH, filepath))
    res = build_hough_space_fom_image(img, shape=(200, 600), val=255)
    print('res', res)

    rgb = np.dstack((((res)).astype(int),np.zeros(res.shape).astype(int),np.zeros(res.shape).astype(int)))  # stacks 3 h x w arrays -> h x w x 3
    imsave(os.path.join(IMG_DIR_PATH, '{}-hough.jpg'.format(filepath)), rgb)

    ind = np.unravel_index(np.argmax(res, axis=None), res.shape)
    print('ind', ind)
