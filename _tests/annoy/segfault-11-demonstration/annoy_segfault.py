from annoy import AnnoyIndex
import numpy as np

# path to values file
VALUES_PATH = 'annoy_segfault_values.txt'
# path to temporary annoy index file
ANNOY_INDEX_PATH = 'test.ann'

NMB_VECTORS = 10
NMB_TREES = 20

t = AnnoyIndex(NMB_VECTORS, metric='manhattan')
with open(VALUES_PATH) as f:
  for line_idx, line in enumerate(f):
    idx, vector = line.strip().split(';')
    idx = int(idx)
    vector = np.fromstring(vector, dtype='float64', sep=' ')
    # using 'line_idx' in the line below instead of 'idx'
    # (i.e., using sequential IDs) fixes the issue
    t.add_item(idx, vector)

t.build(NMB_TREES)
t.save(ANNOY_INDEX_PATH)

# .....

u = AnnoyIndex(NMB_VECTORS, metric='manhattan')
u.load(ANNOY_INDEX_PATH)

# segfault only happens with certain vectors.
# for instance, np.zeros(10) does not segfault.
# the term at index 4 must be approximately >=0.9
# to reproduce the segfault
needle_vector = np.array([0., 0., 0., 0., 0.9, 0., 0., 0., 0., 0.])
needle_vector = needle_vector.astype('float64')

# segfault 11
out = u.get_nns_by_vector(needle_vector, 100)
print out