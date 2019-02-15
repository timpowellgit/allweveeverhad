from scipy import misc
import numpy as np
import pandas as pd
import os
from tqdm import tqdm
import pickle
import scipy
from scipy import spatial
from scipy import io
from scipy.io import wavfile
from itertools import chain
from string import strip
import sys
import operator
from models import db, Image
from multiprocessing import Pool


# DEBUG_INPUT_FILEPATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/4x4.jpg'
# IMG_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-images'
# NEEDLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-images/afl04MNS-LDAfAmrAsdPPQ.jpg'
# PICKLED_HISTOGRAMS_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-histograms.pickle'

ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']
HISTOGRAM_BINS_LIST = [8,16,32,64,128]
USE_DENSITY = True

MULTIPROC_POOL_SIZE = 6

db.init(ARTWORKS_SQLITE_PATH)

def chunks(l, n):
  """Yield successive n-sized chunks from l."""
  for i in range(0, len(l), n):
    yield l[i:i + n]

def get_flat_list_histogram_for_image_path(path, nmb_bins_list):
  try:
    orig_im = misc.imread(path)
  except:
    print 'ERR opening img!!',path
    return None

  nmb_channels = None
  if len(orig_im.shape) == 3 and orig_im.shape[2] == 3:
    nmb_channels = 3
  elif len(orig_im.shape) == 2:
    nmb_channels = 1
  if nmb_channels is None:
    print 'ERR not 1 or 3 chans',path,orig_im.shape
    return None

  histograms_for_bin_numbers = []
  for nmb_bins in nmb_bins_list:
    # make sure that we're dealing with 3 channel images only
    im = orig_im.reshape(orig_im.shape[0] * orig_im.shape[1], nmb_channels)
    c_histograms = [np.histogram(im[:,_], bins=nmb_bins,
            density=USE_DENSITY, range=(0, 255))[0] for _ in range(nmb_channels)]
    if nmb_channels == 1:
      # propagate single channel histogram values into rgb channels
      c_histograms = c_histograms * 3
    histograms_for_bin_numbers.append(np.array(list(chain.from_iterable(c_histograms))))

  return np.array(histograms_for_bin_numbers)

# ---

# def process_dir_pickle():
#   filepaths = os.listdir(IMG_DIR)
#   filepaths = filter(lambda f: f.endswith('.jpg'), filepaths)
#   panda_indices = []
#   panda_values = []

#   for filepath in tqdm(filepaths):
#     histograms = get_flat_list_histogram_for_image_path(os.path.join(IMG_DIR, filepath), HISTOGRAM_BINS_LIST)
#     # some problem while reading the image, skip
#     if histograms is None:
#       continue
 
#     full_filepath = '/mnt/volume-nyc1-01/artsy-images/d32dm0rphc51dk.cloudfront.net/{}/larger.jpg'.format(filepath.replace('.jpg', ''))
#     try:
#       db_index = Image.get(Image.img_local_path == full_filepath).id
#     except:
#       print 'ERR not found',full_filepath
#       continue

#     panda_indices.append(db_index)
#     panda_values.append(histograms)

#   df = pd.DataFrame(panda_values, index=panda_indices,
#             columns=['rgb_hist_{}_bins'.format(_) for _ in HISTOGRAM_BINS_LIST])
#   df.to_pickle(PICKLED_HISTOGRAMS_PATH)

def multi_proc_process_filepaths(arg):
  pool_number, list_of_filepaths, output_pickles_file = arg

  with open(output_pickles_file, 'w') as output_f:
    for filepath in tqdm(list_of_filepaths, desc='pool {}'.format(pool_number), position=pool_number):
      histograms = get_flat_list_histogram_for_image_path(filepath, HISTOGRAM_BINS_LIST)
      # some problem while reading the image (typically, CMYK pictures), skip
      if histograms is None:
        continue

      database_index = Image.get(Image.img_local_path == filepath).id

      # successively dump histogram pickles into output file
      # no need to build up huge arrays!
      pickle.dump((database_index, histograms), output_f)

# step 1 - write all paths/histogram into files of concat'ened pickle dumps
def process_filepath_list_write_to_pickle_files(input_filepath_list_path, output_pickle_file):
  with open(input_filepath_list_path) as f:
    filepaths = map(strip, f.readlines())

  multi_proc_pool = Pool(MULTIPROC_POOL_SIZE)

  lists_of_filepaths = list(chunks(filepaths, len(filepaths)/MULTIPROC_POOL_SIZE))
  print 'len(lists_of_filepaths)',len(lists_of_filepaths)
  output_pickles_files = ['{}-{}.pickle'.format(output_pickle_file, _) for _ in range(MULTIPROC_POOL_SIZE)]

  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # THIS IS BUGGY
  # zip will drop values!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  zip_res = list(zip(range(MULTIPROC_POOL_SIZE), lists_of_filepaths, output_pickles_files))
  print 'len(zip_res)',len(zip_res)

  print 'calling pool map'
  multi_proc_pool.map(multi_proc_process_filepaths,
          zip(range(MULTIPROC_POOL_SIZE), lists_of_filepaths, output_pickles_files))

# STEP 2 DONE IN COLOR HIST 2 PY FILE!!

# (used to be) step 2 - read back paths/histograms and recreate panda dataframe
# def read_txt_file_decode_histograms(input_txt_file):
#   with open(input_txt_file) as f:
#     all_hashes = map(lambda _:_.strip().split(), f.readlines())
#   all_hashes = map(lambda _: (_[0], b64_decode(_[1])), all_hashes)
#   # equivalent of map(operator.itemgetter(0), l) and map(operator.itemgetter(1), l)
#   index, values = map(list, zip(*all_hashes))
#   values = map(lambda _: [_], values)
#   df = pd.DataFrame(values, index=index, columns=['rgb_hist'])
#   print df

#   needle_histogram = get_flat_list_histogram_for_image_path(NEEDLE_PATH)
#   color_hist_dist = scipy.spatial.distance.cdist(df['rgb_hist'].tolist(), [needle_histogram])
#   r_delta = pd.DataFrame(color_hist_dist, index=df.index, columns=['dist'])
#   print r_delta.sort_values('dist')['dist'].index

# def find_needle(needle_path):
#   with open(PICKLED_HISTOGRAMS_PATH) as f:
#     df = pickle.load(f)

#   needle_histogram = get_flat_list_histogram_for_image_path(needle_path)

#   color_hist_dist = scipy.spatial.distance.cdist(df['rgb_hist'].tolist(), [needle_histogram])
#   print('color_hist_dist', color_hist_dist)

#   r_delta = pd.DataFrame(color_hist_dist, index=df.index, columns=['dist'])
#   print r_delta.sort_values('dist')

if __name__ == '__main__':
  # process_dir_pickle()

  # process_dir_pickle()
  # find_needle(NEEDLE_PATH)

  assert len(sys.argv) == 3, 'usage: python {} <LIST_OF_FILEPATHS_FILE> <OUTPUT_PICKLE_FILE_PATTERN>'.format(sys.argv[0])
  assert os.path.isfile(sys.argv[1])
  process_filepath_list_write_to_pickle_files(sys.argv[1], sys.argv[2])

  # assert len(sys.argv) == 2, 'usage python {} <TXT_INPUT_FILE_WITH_PATHS_AND_HASHES>'.format(sys.argv[0])
  # assert os.path.isfile(sys.argv[1])
  # read_txt_file_decode_histograms(sys.argv[1])
