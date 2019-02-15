from annoy import AnnoyIndex
import psutil
import os
import random
import time
import numpy as np
from tqdm import trange

ANNOY_INPUT_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/_annoy_tests/test-tf-redux-10k-pandas.pickle'

# .ann file generated on rgb_hist_64_bins col
NMB_VECTORS = 2048
NMB_EXPERIMENTS = 10000
NMB_TOP_RESULTS = 10

# return the memory usage in MB
def memory_usage_psutil():
  process = psutil.Process(os.getpid())
  mem = process.memory_info()[0] / float(2 ** 20)
  return mem

print 'init!'
print('memory_usage_psutil()', memory_usage_psutil())

print('creating new annoyindex')
t = AnnoyIndex(NMB_VECTORS, metric='euclidean')
print('memory_usage_psutil()', memory_usage_psutil())

print('loading .ann file')
t.load(ANNOY_INPUT_FILE)
print('memory_usage_psutil()', memory_usage_psutil())

print 'getting n items'
nmb_items = t.get_n_items()
print('nmb_items', nmb_items)
print('memory_usage_psutil()', memory_usage_psutil())

# print 'gettng random item vector'
# rand_index = random.randint(0, nmb_items - 1)
# test_vector = t.get_item_vector(rand_index)
# time.sleep(5)
# print('test_vector', len(test_vector))
# print('memory_usage_psutil()', memory_usage_psutil())

# print 'getting top 1 result with default search_k, no distances'
# print len(t.get_nns_by_vector(test_vector, 1))
# time.sleep(5)
# print('memory_usage_psutil()', memory_usage_psutil())

# print 'getting top 100 results with default search_k, no distances'
# print len(t.get_nns_by_vector(test_vector, 100))
# time.sleep(5)
# print('memory_usage_psutil()', memory_usage_psutil())

# print 'getting top 100 results with default search_k, with distances'
# print len(t.get_nns_by_vector(test_vector, 100, include_distances=True))
# time.sleep(5)
# print('memory_usage_psutil()', memory_usage_psutil())


rand_index = random.randint(0, nmb_items - 1)
test_vector = t.get_item_vector(rand_index)

print NMB_EXPERIMENTS,'times: getting top',NMB_TOP_RESULTS,'results with default search_k, with distances'
for _ in trange(NMB_EXPERIMENTS):
  rand_vect = np.random.rand(1, len(test_vector))[0]
  t.get_nns_by_vector(rand_vect, NMB_TOP_RESULTS, include_distances=True)

time.sleep(5)
print('memory_usage_psutil()', memory_usage_psutil())

print 'unloading index'
t.unload()
time.sleep(5)
print('memory_usage_psutil()', memory_usage_psutil())

print 'the end'
