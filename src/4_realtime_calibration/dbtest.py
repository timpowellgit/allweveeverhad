import peewee
import os
import tqdm
import pickle
import math
from collections import defaultdict

from models import db, Artwork, Image
REALTIME_DIFF_PICKLE_PATH = '/Users/timothypowell/allweveeverhad-master/pickle_toss/file0.pickle'#'/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/last_diff_results_for_realtime.pickle'
DIFF_PICKLE_FILES_DIR_PATH = '/Users/timothypowell/allweveeverhad-master/pickle_toss'

ARTWORKS_SQLITE_PATH = '/Users/timothypowell/allweveeverhad-master/serialized_data/artworks.sqlite3'
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

MIDI_CONTROL_TO_ALGO = {
  13: 'image_ratio',
  14: 'multi_hist',
  15: 'lines_angle_hist',
  16: 'lines_vert_dist_hist',
  17: 'lines_horiz_dist_hist',

  31: 'hist_ahash',
  32: 'hist_dhash',
  33: 'hist_phash',
  34: 'hist_whash',

  49: 'tf',
  50: 'hist',
  51: 'ahash',
  52: 'dhash',
  53: 'phash',
  54: 'whash',
}
ALGOS = MIDI_CONTROL_TO_ALGO.values()
# key is algo, value is multiplier
KNOB_MULTIPLIER = defaultdict(lambda:1)

# 0.0 - 1.0 divided into as many intervals as there are faders
FADER_INTERPOLATION_X = [1.0/7*i for i in range(8)]
# default is linear interpolation -- i.e. x=y
FADER_INTERPOLATION_Y = FADER_INTERPOLATION_X[:]
FADER_CHANNEL_MIN = 77
FADER_CHANNEL_MAX = 84

global_transfer_value = 2.8346456692913384
global_input_max = 77.953
global_output_max = 1.299

all_weights = defaultdict(int)
all_weights.update({"ahash":0.787,"dhash":1.102,"hist":17.008,"hist_ahash":0.630,
  "hist_dhash":0.630,"hist_phash":12.441,"hist_whash":0.945,"image_ratio":1.102,
  "lines_angle_hist":5.512,"lines_horiz_dist_hist":3.622,"lines_vert_dist_hist":3.622,
  "multi_hist":6.772,"phash":3.150,"tf":20.000,"whash":0.787})

MAX_ITEMS_TO_SEND_BACK = 50


db.init(ARTWORKS_SQLITE_PATH)





db.init(ARTWORKS_SQLITE_PATH)
print type(Image.get_by_id)
print Image.get_by_id2('309790')
print Image.get_by_id2('1086544')

diff_data = None
diff_data = []
pickle_filepaths = os.listdir(DIFF_PICKLE_FILES_DIR_PATH)
pickle_filepaths = filter(lambda f:f.endswith('.pickle'), pickle_filepaths)
pickle_filepaths.sort(key=lambda _: int(os.path.splitext(_)[0].replace('file', '')))
for pickle_filepath in pickle_filepaths:
	print 'loading pickle files'
	with open(os.path.join(DIFF_PICKLE_FILES_DIR_PATH, pickle_filepath)) as f:
		pickle_data = pickle.load(f)
	print 'normalizing data'
	for algo, factor in NORMALIZATION.items():
		if algo not in pickle_data:
			continue
		pickle_data[algo] = 1 - (pickle_data[algo] / factor)
	diff_data.append(pickle_data)

all_img_data = []

# track_score_of_image_ids_output = []

for diff_img_index, diff_img in enumerate(diff_data):
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
  for x in weighted_ids[:MAX_ITEMS_TO_SEND_BACK].index:
  	print x, type(x)

  	try:
  		print Image.get_by_id(x)
  	except:
  		pass
  #image_db_objects = map(Image.get_by_id, weighted_ids[:MAX_ITEMS_TO_SEND_BACK].index)
  #print Image.get_by_id(weighted_ids[:1].index)        




