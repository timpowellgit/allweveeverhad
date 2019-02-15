import pickle
from tqdm import tqdm
import os
import operator
from string import strip
import shutil

DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/realtime-histogram-processed-scores-all-results'
IMG_PATHS_SRC_TEXT_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/4_realtime_calibration/filepaths_for_result_histogram.txt'
IMG_DEST_DIR = '/Users/greg/Desktop/test great matches'

file_paths = [_ for _ in os.listdir(DIR) if _.endswith('.pickle')]

top_scores = []

with open(IMG_PATHS_SRC_TEXT_FILE) as f:
  txt_line_img_paths = map(strip, f.readlines())

for file_path in tqdm(file_paths):
  full_file_path = os.path.join(DIR, file_path)

  with open(full_file_path) as f:
    d = pickle.load(f)

  scores = d['imgs'][0]['most_common_scores']

  top_score = max(scores, key=operator.itemgetter(0))

  # ALTERNATIVE - copy top score winners nito separate directory
  if float(top_score[0]) > 90:
    text_line_line_idx = full_file_path.split('/')[-1].split('.')[0].replace('file', '')
    path = txt_line_img_paths[int(text_line_line_idx)]
    _, img_file_name = os.path.split(path)
    shutil.copy(path, os.path.join(IMG_DEST_DIR, '{}-{}'.format(top_score[0], img_file_name)))

  # # add top score as many times as it appears in score hist
  top_scores.extend([top_score[0]] * top_score[1])

for _ in top_scores:
  print _