import pickle
import pandas as pd
import operator
import os
from tqdm import tqdm, trange
from annoy import AnnoyIndex

PICKLE_LINE_FILE = '/Volumes/Phatty/ART-freeriots-to-make-more-room-on-tw/multi_hist.line.pickle'
OUTPUT_ANNOY_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/annoy_data/multi_hist.ann'

# going with the same number of trees as regular hist index
NMB_ANNOY_TREES = 25
# 16 bins per channel, 3 channel per square block, 9 square blocks per image
NMB_VECTORS = 16 * 3 * 9

all_data = []

with open(PICKLE_LINE_FILE) as f:
  filesize = os.fstat(f.fileno()).st_size
  tqdm_progress_bar = tqdm(total=filesize, desc='file position')
  last_f_tell = 0
  while True:
    try:
      all_data.append(pickle.load(f))
      tqdm_progress_bar.update(f.tell() - last_f_tell)
      last_f_tell = f.tell()
    except:
      break
  tqdm_progress_bar.close()

print 'read',len(all_data),'lines from pickle files'

print 'un-tangling columns using zip'
indices, values = zip(*all_data)
values = map(lambda _: [_], values)

print 'creating data frame'
df = pd.DataFrame(list(values), index=indices, columns=['multi_hist'])

print 'inserting into annoy index'
t = AnnoyIndex(NMB_VECTORS, metric='euclidean')
for idx in trange(len(indices), desc='annoy index row'):
  t.add_item(indices[idx], values[idx][0])

print 'building annoy index'
t.build(NMB_ANNOY_TREES)

print 'saving annoy index'
t.save(OUTPUT_ANNOY_FILE)
