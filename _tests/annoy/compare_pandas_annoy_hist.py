"""

EXPERIMENTS WITH REAL FULL 7GB HIST NUMPY PICKLE FILE

('NMB_ANNOY_TREES', 10)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 100)
('NMB_EXPERIMENTS', 10)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
scipy times 3.90965988636
annoy times 0.479309725761
set_deltas 4.9

resulting .ann file size: ~~1.8Gb

----------------

('NMB_ANNOY_TREES', 100)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 100)
('NMB_EXPERIMENTS', 1000)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved
scipy times 2.91928286719
annoy times 0.097832788229
set_deltas 4.993

resulting .ann file size: ~~1.8Gb

----------------



running with NMB_ANNOY_TREES=1000 right now
'rebuilding annoy file' is taking forever
huge ram use, huge cpu use
temp.....?? .ann file is 3Gb currently on disk


('NMB_ANNOY_TREES', 1000)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 100)
('NMB_EXPERIMENTS', 10)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved
scipy times 4.82603626251
annoy times 2.05428099632
set_deltas 5.0

!!

final file size is 15Gb.............!!!!!!

------------------------------

('NMB_ANNOY_TREES', 100)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 1000)
('NMB_EXPERIMENTS', 10)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved, time: 432.148562908
scipy times 3.89876480103
annoy times 2.44247639179
set_deltas 5.0

file size: 3.24gb

-----------------------------

('NMB_ANNOY_TREES', 50)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 1000)
('NMB_EXPERIMENTS', 50)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved, time: 233.838959932
scipy times 3.58778676033
annoy times 0.738393826485
set_deltas 5.0
.ann filesize 2540889392

-----------------------------

getting there..........!!!! still good in terms of accuracy even with 'reduced' file size

('NMB_ANNOY_TREES', 25)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 1000)
('NMB_EXPERIMENTS', 100)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved, time: 143.65102005
scipy times 3.48474713087
annoy times 0.456097617149
set_deltas 5.0
.ann filesize 2190810960

------------------------------

(venv) g:_annoy_tests (master) $ p compare_pandas_annoy.py 
('NMB_ANNOY_TREES', 12)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 1000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved, time: 90.3428490162
scipy times 3.49683836699
annoy times 0.258180836439
set_deltas 4.99
.ann filesize 2008736528

---------------------------

('NMB_ANNOY_TREES', 12)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
scipy times 3.71485638738
annoy times 0.53115038991
set_deltas 4.99
.ann filesize 2008736528

------------------------------

('NMB_ANNOY_TREES', 10)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved, time: 124.160251856
scipy times 4.38545897603
annoy times 0.580873177052
set_deltas 4.995
.ann filesize 1980651536

------------------------------

('NMB_ANNOY_TREES', 8)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved, time: 73.5903232098
scipy times 3.02800825
annoy times 0.334944399595
set_deltas 4.995
.ann filesize 1952582064

------------------------------------

NOTES:
under 12 trees, build size seems to stay constant at 1.9Gb
for all 1M values of rgb_hist_128_bins
average of set_deltas is very good with 10k search_k_factor (4.99 - 4.995)
when doing 200 experiments

25 trees had perfect score of 5.0 with 100 experiments and a 2.2Gb file

-------------------------------------

25 trees of rgb_hist_64_bins results in 1.2Gb file
25 trees of rgb_hist_128_bins results in 2.2Gb file

---------------------------------------

FINAL GOOD ENOUGH PARAMS FOR HIST:

('NMB_ANNOY_TREES', 25)
('NMB_TOP_RESULTS_TO_COMPARE', 5)
('SEARCH_K_FACTOR', 10000)
('NMB_EXPERIMENTS', 200)
loading histogram data
done loading histogram data
('nmb rows', 1177200)
rebuilding annoy file
saved, time: 131.094130039
scipy times 1.80483155251
annoy times 0.374527094364
set_deltas 5.0
.ann filesize 1280096384

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

HISTOGRAM_PICKLES_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/complete_histograms.pickle-pandas'
ANNOY_OUTPUT_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/_annoy_tests/test.ann'

RECREATE_ANNOY_FILE = True
NMB_ANNOY_TREES = 25
NMB_TOP_RESULTS_TO_COMPARE = 5
SEARCH_K_FACTOR = 10000
NMB_EXPERIMENTS = 200

print('NMB_ANNOY_TREES', NMB_ANNOY_TREES)
print('NMB_TOP_RESULTS_TO_COMPARE', NMB_TOP_RESULTS_TO_COMPARE)
print('SEARCH_K_FACTOR', SEARCH_K_FACTOR)
print('NMB_EXPERIMENTS', NMB_EXPERIMENTS)

print 'loading histogram data'
with open(HISTOGRAM_PICKLES_PATH) as f:
  histogram_data = pickle.load(f)
print 'done loading histogram data'

histogram_col = histogram_data['rgb_hist_64_bins']
histogram_index = list(histogram_col.index)
histogram_values = list(histogram_col.values)

assert len(histogram_index) == len(histogram_values)

print('nmb rows', len(histogram_index))

nmb_vectors = len(histogram_values[0])
print('nmb_vectors', nmb_vectors)

if RECREATE_ANNOY_FILE:
  print 'rebuilding annoy file'
  start = timer()
  t = AnnoyIndex(nmb_vectors, metric='euclidean')
  for i, v in zip(histogram_index, histogram_values):
    t.add_item(i, v)

  # nmb trees
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
  needle_row_index = random.randint(0, len(histogram_index) - 1)
  needle_index, needle_histogram = map(lambda _: _[needle_row_index], [histogram_index, histogram_values])

  # 'perfect' calculation using numpy
  start = timer()
  hist_dist = scipy.spatial.distance.cdist(histogram_col.tolist(), [needle_histogram])
  delta_df = pd.DataFrame(hist_dist, index=histogram_col.index, columns=['dist_scipy'])
  end = timer()
  scipy_times.append(end - start)

  # approximate dist calculation using annoy
  start = timer()
  u = AnnoyIndex(nmb_vectors, metric='euclidean')
  u.load(ANNOY_OUTPUT_FILE)
  hist_delta = u.get_nns_by_vector(needle_histogram, NMB_TOP_RESULTS_TO_COMPARE,
                        search_k=NMB_ANNOY_TREES * NMB_TOP_RESULTS_TO_COMPARE * SEARCH_K_FACTOR,
                        include_distances=True)
  end = timer()
  annoy_times.append(end - start)

  delta_df_annoy = pd.DataFrame(hist_delta[1], index=hist_delta[0], columns=['dist_annoy'])

  merged_pd = pd.concat([delta_df, delta_df_annoy], axis=1)

  scipy_set = set(merged_pd.sort_values('dist_scipy').index[:NMB_TOP_RESULTS_TO_COMPARE])
  annoy_set = set(merged_pd.sort_values('dist_annoy').index[:NMB_TOP_RESULTS_TO_COMPARE])

  set_deltas.append(len(scipy_set.intersection(annoy_set)))

print 'scipy times', sum(scipy_times)/float(len(scipy_times))
print 'annoy times', sum(annoy_times)/float(len(annoy_times))
print 'set_deltas', sum(set_deltas)/float(len(set_deltas))

statinfo = os.stat(ANNOY_OUTPUT_FILE)
print '.ann filesize', statinfo.st_size
