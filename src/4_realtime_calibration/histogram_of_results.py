import sys
import pickle
import mido
from collections import defaultdict, OrderedDict
import math
import json
from models import db, Artwork, Image
import os
from tqdm import tqdm
import numpy as np
import re
from collections import Counter, OrderedDict
from string import strip
from web_server import process_image_file

PICKLE_SCORES_DEST_DIR_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/realtime-histogram-processed-scores-post-apr18'
DIFF_PICKLE_FILES_DIR_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/realtime-multi-pickles'
ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3'

# ---

ALGOS = ['image_ratio',
'multi_hist',
'lines_angle_hist',
'lines_vert_dist_hist',
'lines_horiz_dist_hist',
'hist_ahash',
'hist_dhash',
'hist_phash',
'hist_whash',
'tf',
'hist',
'ahash',
'dhash',
'phash',
'whash',]

NORMALIZATION = {
  # max euclidean distance to 2048 dimensions
  'tf': math.sqrt(2048),
  # unsure of current normalization, but values are small enough
  'hist': 1,
  'ahash': 64,
  'dhash': 64,
  'phash': 64,
  'whash': 64,
  'hist_ahash': 1,
  'hist_dhash': 1,
  'hist_phash': 1,
  'hist_whash': 1,

  'image_ratio': 1,
  'multi_hist': 1,
  'lines_angle_hist': 64,
  'lines_vert_dist_hist': 64,
  'lines_horiz_dist_hist': 64,
}

# ---

db.init(ARTWORKS_SQLITE_PATH)

# ---

# OK TO SET DEFAULTS HERE
# global_transfer_value = 1
# global_input_max = 100.0
# global_output_max = 100.0

global_transfer_value = 2.8346456692913384
global_input_max = 77.953
global_output_max = 1.299

all_weights = defaultdict(int)
all_weights.update({"ahash":0.787,"dhash":1.102,"hist":17.008,"hist_ahash":0.630,"hist_dhash":0.630,"hist_phash":12.441,"hist_whash":0.945,"image_ratio":1.102,"lines_angle_hist":5.512,"lines_horiz_dist_hist":3.622,"lines_vert_dist_hist":3.622,"multi_hist":6.772,"phash":3.150,"tf":20.000,"whash":0.787})
# / DEFAULTS

def realtime_pickle_init(pickle_filepath):
  diff_data = []
  print 'loading values from pickle file'
  with open(pickle_filepath) as f:
    pickle_data = pickle.load(f)
  print 'normalizing dist values'
  for algo, factor in NORMALIZATION.items():
    if algo not in pickle_data:
      continue
    pickle_data[algo] = 1 - (pickle_data[algo] / factor)
  diff_data.append(pickle_data)
  return diff_data

def realtime_pickle_process(diff_data):
  global global_transfer_value
  global global_input_max
  global global_output_max
  
  all_img_data = []
  for diff_img in diff_data:
    weighted_ids = []
    for algo in ALGOS:
      # algo can be not in the pickled diff data
      # as lines only outputs columns for horiz or vert if
      # there were vert or horiz lines found...
      if algo not in diff_img:
        continue

      # (knob * algo_diff) ** transfer
      img_algo_result = (diff_img[algo].fillna(0) ** global_transfer_value) * all_weights[algo]
      # linearly transpose all results
      img_algo_result = (img_algo_result / global_input_max) * global_output_max

      # add weighted col to output
      weighted_ids.append(img_algo_result)

    # squish weighted values
    weighted_ids = sum(weighted_ids)
    weighted_ids = weighted_ids.sort_values(ascending=False)


    # get the match score for 10 matching images (per src img)
    # top_match_scores = weighted_ids[:10].values

    # alternative: only return results > 50%
    # top_match_scores = weighted_ids[weighted_ids > .5].values

    # alternative: all results
    top_match_scores = weighted_ids.values


    # convert to percentage
    percentage_match_scores = top_match_scores * 100.0
    # stringify matches (too long of a float will mess with table/td width output)
    percentage_match_scores_float_str = map(lambda _: '%.1f' % _, percentage_match_scores)

    c = Counter(percentage_match_scores_float_str)
    most_common_scores = c.most_common()

    per_img_data = {
      'most_common_scores': most_common_scores,
    }
    all_img_data.append(per_img_data)

  # send back new results
  return {
    'imgs': all_img_data,
    'weights': OrderedDict([(k, '%.3f' % all_weights[k]) for k in sorted(all_weights)]),
    'transfer_info': [(_, '%.1f' % (_/10.0) ** global_transfer_value) for _ in range(10)],
    'transfer_value': global_transfer_value,
    'global_input_max': '%.1f' % (global_input_max * 100.0),
    'global_output_max': '%.1f' % (global_output_max * 100.0),
  }

if __name__ == '__main__':
  assert len(sys.argv) == 2, 'usage: python {} list_of_filepaths.txt'

  all_image_filepaths = []
  with open(sys.argv[1]) as f:
    all_image_filepaths = map(strip, f)

  for image_idx, image_filepath in enumerate(tqdm(all_image_filepaths)):
    # FIXME SKIP PROCESSED IMAGES
    if image_idx < 2008:
      continue

    img_file_key = 'file{}'.format(image_idx)
    output_pickle_path = process_image_file(image_filepath, 16, img_file_key)

    diff_data = realtime_pickle_init(output_pickle_path)
    res = realtime_pickle_process(diff_data)
    pickle_results_out_file_path = os.path.join(PICKLE_SCORES_DEST_DIR_PATH, '{}.pickle'.format(img_file_key))
    with open(pickle_results_out_file_path, 'w') as f:
      pickle.dump(res, f)

    os.remove(output_pickle_path)
