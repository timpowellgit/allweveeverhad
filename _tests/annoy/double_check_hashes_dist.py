import pickle
import random
import numpy as np
from annoy import AnnoyIndex
import pandas as pd

ALGO = 'phash'
NMB_VECTORS = 64

PICKLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_and_met_hashes_pandas.pickle'
ANNOY_INDEX_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/annoy_data/imagehash/imagehash_{}.ann'.format(ALGO)

print 'loading pickle file'
with open(PICKLE_PATH) as f:
  pandas_data = pickle.load(f)

needle_index = random.choice(pandas_data.index)
needle_value = pandas_data[ALGO][needle_index].reshape(-1,64)

hashes_as_np_array = np.array(pandas_data[ALGO])
all_hashes_as_np = np.stack(hashes_as_np_array).reshape((-1,64))

print('len(all_hashes_as_np)', len(all_hashes_as_np))

print 'computing numpy diff'
hashes_pure_diff = np.count_nonzero(all_hashes_as_np != needle_value, axis=1)
pandas_pure_diff = pd.DataFrame(hashes_pure_diff, index=pandas_data[ALGO].index)
pandas_pure_diff = pandas_pure_diff.sort_index()
print 'pandas_pure_diff'
print pandas_pure_diff

print 'loading annoy file, getting NNs by needle vector'
annoy_index = AnnoyIndex(NMB_VECTORS, metric='hamming')
annoy_index.load(ANNOY_INDEX_PATH)
annoy_results = annoy_index.get_nns_by_vector(needle_value.flatten(),
  len(all_hashes_as_np),
  include_distances=True)

print 'creating annoy dist dataframe'
pandas_annoy_results = pd.DataFrame(
  map(int, annoy_results[1]),
  index=annoy_results[0])

pandas_annoy_results = pandas_annoy_results.sort_index()
print 'pandas_annoy_results'
print pandas_annoy_results

print 'pure diff and annoy diff is the same:',\
  (pandas_pure_diff == pandas_annoy_results).all()
