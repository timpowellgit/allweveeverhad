"""

EXPERIMENTS WITH REDUX 80MB 10k rows TF NUMPY PICKLE FILE

('NMB_ANNOY_TREES', 25)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
`loading histogram data
done loading histogram data
('nmb rows', 10000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 36.7999608517
scipy times 0.14292488575
annoy times 0.0738178014755
set_deltas 5.0
.ann filesize 9735246144

------------

('NMB_ANNOY_TREES', 12)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 10000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 34.742279768
scipy times 0.140210249424
annoy times 0.0678590738773
set_deltas 5.0
.ann filesize 9733620960

---------

('NMB_ANNOY_TREES', 6)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 10000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 28.911687851
scipy times 0.13952002883
annoy times 0.0654361522198
set_deltas 5.0
.ann filesize 9732865824

---------

('NMB_ANNOY_TREES', 3)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 10000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 26.3946208954
scipy times 0.146129345894
annoy times 0.0668388807774
set_deltas 5.0
.ann filesize 9732488256

---------------

('NMB_ANNOY_TREES', 2)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 10000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 24.7143311501
scipy times 0.145463644266
annoy times 0.0657143938541
set_deltas 5.0
.ann filesize 9732373344

---------------

('NMB_ANNOY_TREES', 1)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 10000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 25.9161329269
scipy times 0.14787040472
annoy times 0.0670252001286
set_deltas 5.0
.ann filesize 9732258432

---------------

('NMB_ANNOY_TREES', 1)
('NMB_TOP_RESULTS_TO_COMPARE', 20)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 10000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 25.3135130405
scipy times 0.147777700424
annoy times 0.0657820022106
set_deltas 20.0
.ann filesize 9732258432

---------------

('NMB_ANNOY_TREES', 1)
('NMB_TOP_RESULTS_TO_COMPARE', 100)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 100)
loading histogram data
done loading histogram data
('nmb rows', 10000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 27.9744951725
scipy times 0.146327338219
annoy times 0.0733173561096
set_deltas 100.0
.ann filesize 9732258432

===============================


very large number of vectors leads to results always being perfect,
but filesize being very large (9gb compared to original 80mb pandas pickle file...)

memory test: very very small memory used (30Mb...???)

seems like data was written in a very efficient way on disk, taking up enormous amounts of size
which leads to fast access (about half of the time of numpy) and small memory footprint

================================

USING 100k file now..............

('NMB_ANNOY_TREES', 1)
('NMB_TOP_RESULTS_TO_COMPARE', 100)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 100)
loading histogram data
done loading histogram data
('nmb rows', 100000)
('nmb_vectors', 2048)
rebuilding annoy file
saved, time: 58.4107220173
scipy times 2.79824609518
annoy times 0.893993279934
set_deltas 100.0
.ann filesize 9734187312

took 10x times the time to search (annoy still faster than numpy) and double the time to create the index

but the file size is almost identical......... it only depends on the number of vectors!!!!

fantastic.........!!!!!!!!!!!!!!!!!!!!!!

"""

from annoy import AnnoyIndex
import pickle
import random
from timeit import default_timer as timer
import scipy
from scipy import spatial
import pandas as pd
from tqdm import trange
import os

TF_PICKLES_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/tf-redux-100k-pandas.pickle'
ANNOY_OUTPUT_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/_annoy_tests/test-tf-redux-100k-pandas.af'

RECREATE_ANNOY_FILE = True
NMB_ANNOY_TREES = 1
NMB_TOP_RESULTS_TO_COMPARE = 100
SEARCH_K_FACTOR = 10000
NMB_EXPERIMENTS = 100

print('NMB_ANNOY_TREES', NMB_ANNOY_TREES)
print('NMB_TOP_RESULTS_TO_COMPARE', NMB_TOP_RESULTS_TO_COMPARE)
print('SEARCH_K_FACTOR', SEARCH_K_FACTOR)
print('NMB_EXPERIMENTS', NMB_EXPERIMENTS)

print 'loading tf data'
with open(TF_PICKLES_PATH) as f:
  tf_data = pickle.load(f)
print 'done loading tf data'

tf_col = tf_data['tf']
tf_index = list(tf_col.index)
tf_values = list(tf_col.values)

assert len(tf_index) == len(tf_values)

print('nmb rows', len(tf_index))

nmb_vectors = len(tf_values[0])
print('nmb_vectors', nmb_vectors)

if RECREATE_ANNOY_FILE:
  print 'rebuilding annoy file'
  start = timer()
  t = AnnoyIndex(nmb_vectors, metric='euclidean')
  for i, v in zip(tf_index, tf_values):
    t.add_item(i, v)

  t.build(NMB_ANNOY_TREES)
  t.save(ANNOY_OUTPUT_FILE)
  end = timer()
  print 'saved, time:',end-start

#################################
#################################
#################################



set_deltas = []
scipy_times = []
annoy_times = []
for test_idx in trange(NMB_EXPERIMENTS):
  # randomly pick needle
  needle_row_index = random.randint(0, len(tf_index) - 1)
  needle_index, needle_histogram = map(lambda _: _[needle_row_index], [tf_index, tf_values])

  # 'perfect' calculation using numpy
  start = timer()
  tf_dist = scipy.spatial.distance.cdist(tf_col.tolist(), [needle_histogram])
  delta_df = pd.DataFrame(tf_dist, index=tf_col.index, columns=['dist_scipy'])
  end = timer()
  scipy_times.append(end - start)

  # approximate dist calculation using annoy
  start = timer()
  u = AnnoyIndex(nmb_vectors, metric='euclidean')
  u.load(ANNOY_OUTPUT_FILE)
  tf_delta = u.get_nns_by_vector(needle_histogram, NMB_TOP_RESULTS_TO_COMPARE,
                        search_k=NMB_ANNOY_TREES * NMB_TOP_RESULTS_TO_COMPARE * SEARCH_K_FACTOR,
                        include_distances=True)
  end = timer()
  annoy_times.append(end - start)

  delta_df_annoy = pd.DataFrame(tf_delta[1], index=tf_delta[0], columns=['dist_annoy'])

  merged_pd = pd.concat([delta_df, delta_df_annoy], axis=1)

  scipy_set = set(merged_pd.sort_values('dist_scipy').index[:NMB_TOP_RESULTS_TO_COMPARE])
  annoy_set = set(merged_pd.sort_values('dist_annoy').index[:NMB_TOP_RESULTS_TO_COMPARE])

  set_deltas.append(len(scipy_set.intersection(annoy_set)))

print 'scipy times', sum(scipy_times)/float(len(scipy_times))
print 'annoy times', sum(annoy_times)/float(len(annoy_times))
print 'set_deltas', sum(set_deltas)/float(len(set_deltas))

statinfo = os.stat(ANNOY_OUTPUT_FILE)
print '.ann filesize', statinfo.st_size
