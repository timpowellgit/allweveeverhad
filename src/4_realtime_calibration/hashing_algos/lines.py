import math
import numpy as np
import operator
from skimage import color, filters
from skimage.transform import hough_line, hough_line_peaks
from skimage.transform import resize
from skimage.io import imread
from skimage.exposure import equalize_adapthist
import sys
import skimage

def get_sub_rect(img, x0, y0, width, height):
  return np.copy(img[y0:y0 + height, x0:x0 + width])

# do hough line transform on "inside" of image so as not to match image's natural sides/frame
def remove_margin(img, margin):
  y,x = img.shape
  return img[margin:margin+(y-margin*2),margin:margin+(x-margin*2)]

def get_hough_line_vectors(image_path):
  img = imread(image_path)

  img = resize(img, (512,512))

  if len(img.shape) == 2:
    img = np.dstack((img, img, img))

  img_hsv = color.rgb2hsv(img)

  # extract s channel
  img_s = img_hsv[..., 1]

  img_equalized = equalize_adapthist(img_s)

  # images passed to threshold_sauvola must be uint8
  # float64 values sometimes give NaN output......!!!!!!
  # https://github.com/scikit-image/scikit-image/issues/3007
  img_equalized = (img_equalized * 255).astype('uint8')
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

  # no angles found, hence no lines found
  if np.all(angle_hist == 0):
    return None

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
    'angle_hist': angle_hist.astype('float64'),
    'horiz_dist_hist': horiz_dist_hist.astype('float64'),
    'vert_dist_hist': vert_dist_hist.astype('float64')
  }

if __name__ == '__main__':
  print get_hough_line_vectors(sys.argv[1])
