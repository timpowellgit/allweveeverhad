import imageio
import numpy as np
from itertools import chain
import sys
import scipy
from scipy import spatial


BINNING = [8,16,32,64,128]

# used for both hist and multi hist
HIST_USE_DENSITY = True

MULTI_HIST_NMB_BINS = 16

def generate_hist_from_im(im, nmb_bins):
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

  c_histograms = [np.histogram(im[:,_], bins=nmb_bins,
                                  density=HIST_USE_DENSITY, range=(0,255))[0] \
                                                  for _ in range(nmb_channels)]

  if nmb_channels == 1:
    # propagate single channel histogram values into rgb channels
    c_histograms = c_histograms * 3

  return np.array(list(chain.from_iterable(c_histograms)))

def generate_hist(image_path, nmb_bins):
  im = imageio.imread(image_path)
  return generate_hist_from_im(im, nmb_bins)

def get_sub_rect(img, x0, y0, width, height):
  return np.copy(img[y0:y0 + height, x0:x0 + width])

def generate_multi_hist(image_path):
  im = imageio.imread(image_path)
  h, w = im.shape[:2]
  x_delta = w/3
  y_delta = h/3
  muli_hist_vect = []
  skip_image = False
  for x_idx in range(3):
    if skip_image:
      break
    for y_idx in range(3):
      sub_img = get_sub_rect(im, x0=x_idx*x_delta, y0=y_idx*y_delta, width=x_delta, height=y_delta)
      hist_vector = generate_hist_from_im(sub_img, MULTI_HIST_NMB_BINS)
      if hist_vector is None:
        skip_image = True
        break
      muli_hist_vect.append(hist_vector)
  if skip_image:
    return None
  img_multi_hist_vect = np.array(list(chain.from_iterable(muli_hist_vect)))
  return img_multi_hist_vect


if __name__ == '__main__':
  # hist
  for nmb_bins in BINNING:
    v1 = generate_hist(sys.argv[1], nmb_bins)
    v2 = generate_hist(sys.argv[2], nmb_bins)
    print 'HIST nmb_bins',nmb_bins,'distance',scipy.spatial.distance.cdist([v1], [v2])

  # multi hist
  v1 = generate_multi_hist(sys.argv[1])
  v2 = generate_multi_hist(sys.argv[2])  
  print 'MULTI HIST distance',scipy.spatial.distance.cdist([v1], [v2])
