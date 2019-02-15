import numpy as np
import os
import skimage
from skimage.io import imread, imsave
from skimage.color import rgb2grey
from skimage.draw import line
import numpy as np
from skimage.transform import (hough_line, hough_line_peaks,
                               probabilistic_hough_line)
from skimage.transform import resize
from skimage.feature import canny
from skimage import data
import matplotlib.pyplot as plt
from matplotlib import cm
from skimage.exposure import equalize_adapthist
import math
from skimage import color
from skimage import filters
from collections import defaultdict
import operator
from tqdm import tqdm
from skimage import util

# Constructing test image
image = np.zeros((100, 100))
idx = np.arange(25, 75)
image[idx[::-1], idx] = 255
image[idx, idx] = 255

def remove_margin(img,margin):
  y,x = img.shape
  return img[margin:margin+(y-margin*2),margin:margin+(x-margin*2)]

DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/allpainters-scraping/img'
# DIR = '/Users/greg/Desktop/hough-test-imgs/new tests to understand dist'
filepaths = sorted(filter(lambda _:_.endswith('.jpg'), os.listdir(DIR)))
filepaths = ['img049.jpg','white-center.jpg','no-17-1961(1).jpg','tentacles-of-memory.jpg','no-20-1957.jpg','no-21.jpg','street-scene.jpg','slow-swirl-at-the-edge-of-the-sea(1).jpg',]
for filepath in filepaths:
  print('filepath', filepath)

  img = imread(os.path.join(DIR, filepath))

  img = resize(img, (512,512))

  if len(img.shape) == 2:
    img = np.dstack((img, img, img))

  img_hsv = color.rgb2hsv(img)

  imsave('{}-hsv.jpg'.format(os.path.join(DIR, 'lines', filepath)), img_hsv)

  # extract s channel
  # FIXME should extract s instead of v???????
  img_s = img_hsv[..., 1]

  imsave('{}-s.jpg'.format(os.path.join(DIR, 'lines', filepath)), img_s)

  img_equalized = equalize_adapthist(img_s)

  imsave('{}-eq.jpg'.format(os.path.join(DIR, 'lines', filepath)), img_equalized)

  thres_sauvola_value = filters.threshold_sauvola(img_equalized)
  img_binarized = img_equalized <= thres_sauvola_value

  image = img_binarized

  image = remove_margin(image, 20)

  # Classic straight-line Hough transform
  h, theta, d = hough_line(image)

  # Generating figure 1
  fig, ax = plt.subplots()
  ax.imshow(image, cmap=cm.gray)

  h, angle, dist = hough_line_peaks(h, theta, d)
  results = zip(h, angle, dist)
  # only keep top 10 results
  results = results[:10]
  # abs angles
  results = filter(lambda (h,angle,dist): (abs(angle) < 0.1) or (abs(angle) > 1.4), results)
  # hough """score""" is (empirically) """high""" enough 
  results = filter(lambda (h,angle,dist): h > 300, results)

  all_angles = map(operator.itemgetter(1), results)
  # turn all angles absolute
  # this doesn't work for 45 degree angles (which we don't care about)
  # but does 'fold' horiz (near 0) and vertical (near 90 and -90) lines degrees together
  all_angles = map(abs, all_angles)
  angle_hist = np.histogram(all_angles, range=(0,math.pi/2), density=False)[0]
  print 'angle_hist'
  print angle_hist

  vert_results = []
  horiz_results = []
  for h,angle,dist in results:
    # do the abs!!!!!!!!!!!!!!!!
    if abs(angle) < math.pi/4:
      print 'vert',(h,angle,dist)
      vert_results.append((h,angle,dist))
    else:
      print 'horiz',(h,angle,dist)
      horiz_results.append((h,angle,dist))

  # distances are in range -diag,diag
  max_dist = math.sqrt(image.shape[0]**2 + image.shape[1]**2)

  # normalize distances according to diag
  # same as with angles, fold hough dist dimension upon itself......
  all_horiz_dist = map(lambda _: abs(_[2]/max_dist), horiz_results)
  all_vert_dist = map(lambda _: abs(_[2]/max_dist), vert_results)

  print('all_horiz_dist', all_horiz_dist)

  horiz_dist_hist = np.histogram(all_horiz_dist, range=(0,1), density=False)[0]
  print 'horiz_dist_hist'
  print horiz_dist_hist

  vert_dist_hist = np.histogram(all_vert_dist, range=(0,1), density=False)[0]
  print 'vert_dist_hist'
  print vert_dist_hist

  for _, angle, dist in results:
    print('_', _)
    y0 = (dist - 0 * np.cos(angle)) / np.sin(angle)
    y1 = (dist - image.shape[1] * np.cos(angle)) / np.sin(angle)
    ax.plot((0, image.shape[1]), (y0, y1), '-r')

  ax.set_xlim((0, image.shape[1]))
  ax.set_ylim((image.shape[0], 0))
  ax.set_axis_off()
  ax.set_title('Detected lines')

  plt.savefig(os.path.join(DIR, 'lines', '{}-ang-{}-horiz-{}-vert-{}.jpg'.format(filepath,
    ','.join(map(lambda _:'{:.1f}'.format(_),angle_hist[~np.isnan(angle_hist)])),
    ','.join(map(lambda _:'{:.1f}'.format(_),horiz_dist_hist[~np.isnan(horiz_dist_hist)])),
    ','.join(map(lambda _:'{:.1f}'.format(_),vert_dist_hist[~np.isnan(vert_dist_hist)])))))
  plt.close()

