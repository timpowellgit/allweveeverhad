import pandas as pd
import numpy as np
from annoy import AnnoyIndex


NMB_VECTOR_ROWS = 2 * 10**6
NMB_VECTORS = 64

ANNOY_INDEX_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/_annoy_tests/imagehash_annoy_to_numpy_diff_to_find_nmb_trees.ann'
NMB_ANNOY_TREES = 1
SEARCH_K_FACTOR = 1
NMB_TOP_RESULTS_TO_COMPARE = NMB_VECTOR_ROWS


# generate 2M random bool arrays
all_vectors = np.random.rand(NMB_VECTOR_ROWS, NMB_VECTORS) > 0.5
print('all_vectors[0]', all_vectors[0])

# generate needle
needle = np.random.rand(1, NMB_VECTORS) > 0.5
print('needle', needle)

# determine perfect distance using count non zero
numpy_diff = np.count_nonzero(needle != all_vectors, axis=1)
pandas_numpy_diff = pd.DataFrame(numpy_diff, index=range(NMB_VECTOR_ROWS), columns=['np'])

# create annoy index using 2m arrays
annoy_index = AnnoyIndex(NMB_VECTORS, metric='hamming')
for idx, v in enumerate(all_vectors):
  annoy_index.add_item(idx, v)
annoy_index.build(NMB_ANNOY_TREES)
# save annoy index (also to check file size)
annoy_index.save(ANNOY_INDEX_PATH)

########

# search for needle

annoy_index = AnnoyIndex(NMB_VECTORS, metric='hamming')
annoy_index.load(ANNOY_INDEX_PATH)
annoy_dist_results = annoy_index.get_nns_by_vector(needle[0],
  NMB_TOP_RESULTS_TO_COMPARE,
  search_k=NMB_ANNOY_TREES * NMB_TOP_RESULTS_TO_COMPARE * SEARCH_K_FACTOR,
  include_distances=True)

pandas_annoy_diff = pd.DataFrame(map(int, annoy_dist_results[1]),
  index=annoy_dist_results[0],
  columns=['annoy'])

# compare top (all at this point..!) results if identical
pandas_diff = pandas_annoy_diff.join(pandas_numpy_diff)
print (pandas_diff['annoy'] == pandas_diff['np']).all()
print('len(pandas_diff)', len(pandas_diff))

# determine nmb_trees necessary to get good results
### 1 is enough....!!!
### end file is 66 Mb for 2M 64 bit vectors
### no search_k_factor necessary
