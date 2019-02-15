import pickle
import os
from annoy import AnnoyIndex
from tqdm import tqdm


HASHES_PICKLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_and_met_hashes_pandas.pickle'
ANNOY_INDEX_DEST_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/annoy_data/imagehash'

NMB_VECTORS = 64
NMB_ANNOY_TREES = 1

# read pickle file containing all hash data
print 'loading pickles file'
with open(HASHES_PICKLE_PATH) as f:
  pandas_data = pickle.load(f)

# for each hash algo col, create new annoy index
for col in tqdm(pandas_data, desc='hash algo', total=len(list(pandas_data))):
  annoy_index = AnnoyIndex(NMB_VECTORS, metric='hamming')
  for index, value in tqdm(pandas_data[col].iteritems(),
    desc='panda row',
    total=len(pandas_data[col])):
    annoy_index.add_item(index, value.flatten())
  annoy_index.build(NMB_ANNOY_TREES)

  annoy_index_path = os.path.join(ANNOY_INDEX_DEST_DIR,
    'imagehash_{}.ann'.format(col))
  annoy_index.save(annoy_index_path)
