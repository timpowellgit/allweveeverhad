import os
import json
from tqdm import tqdm
import pickle

JSON_SRC_DIR_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/MET/api-images-json'
JSON_DATA_PICKLE_FILEPATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/met_artwork_to_img_json_data.pickle'

print 'listing filenames...'
filenames = filter(lambda _: 'additionalImages?crdId=' in _, os.listdir(JSON_SRC_DIR_PATH))

all_data_out = {}
no_results_count = 0

print 'processing...'

for filename in tqdm(filenames):
  with open(os.path.join(JSON_SRC_DIR_PATH, filename)) as f:
    data = json.load(f)
    crd_id = data['request']['crdId']
    if data.get('results') is None or not len(data['results']):
      no_results_count += 1
      continue
    assert crd_id not in all_data_out, ('ERR duplicate crdid', crd_id, filename)
    all_data_out[crd_id] = [(r['originalImageUrl'], r['isOasc']) for r in data['results']]

print('no_results_count', no_results_count)

print 'pickling...'
with open(JSON_DATA_PICKLE_FILEPATH, 'w') as f:
  pickle.dump(all_data_out, f)
