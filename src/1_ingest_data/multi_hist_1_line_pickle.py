from models import db, Artwork, Image
from tqdm import tqdm
import pickle
import os
from get_image_size import get_image_metadata
import imageio
import numpy as np
from itertools import chain
import sys
import scipy
from scipy import spatial
import operator

DEBUG = False
NMB_BINS = 16
HIST_USE_DENSITY = True


if DEBUG:
  ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3'
  OUTPUT_LINE_PICKLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/multi_hist.lines.pickle'
else:
  ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']
  OUTPUT_LINE_PICKLE_PATH = os.environ['OUTPUT_LINE_PICKLE_PATH']


db.init(ARTWORKS_SQLITE_PATH)

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

all_db_image_ids_paths = Image.select(Image.id, Image.img_local_path).order_by(Image.id).tuples()

if DEBUG:
  dir = '/Volumes/Phatty/ART-freeriots-to-make-more-room-on-tw/___scans and real artworks from adam/4 even newer scans/computer2/'
  all_db_image_ids_paths = [(_, os.path.join(dir, 'comp2img{:03d}.jpg'.format(_))) for _ in range(1, 20)]
  all_db_image_ids_paths = [all_db_image_ids_paths[0], (99,'/Users/greg/Desktop/Grayscale_8bits_palette_sample_image.png')]


with open(OUTPUT_LINE_PICKLE_PATH, 'a') as f:
  for image_id, image_path in tqdm(list(all_db_image_ids_paths)[-1000:]):
    if image_path == '':
      continue
    try:
      im = imageio.imread(image_path)
    except:
      print 'ERR',image_id,image_path
      continue
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
        hist_vector = generate_hist(sub_img)
        if hist_vector is None:
          skip_image = True
          break
        muli_hist_vect.append(hist_vector)
    if skip_image:
      continue
    img_multi_hist_vect = np.array(list(chain.from_iterable(muli_hist_vect)))
    pickle.dump((image_id, img_multi_hist_vect), f)
