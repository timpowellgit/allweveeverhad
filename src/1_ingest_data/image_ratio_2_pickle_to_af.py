import pickle
import pandas as pd
import operator
import os
from tqdm import tqdm, trange
from annoy import AnnoyIndex

PICKLE_LINE_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/image_ratio.line.pickle'
OUTPUT_ANNOY_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/annoy_data/image_ratio.ann'

NMB_ANNOY_TREES = 1

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

print 'creating data frame'
df = pd.DataFrame(list(values), index=indices, columns=['image_ratio'])

print 'appending to annoy index'
t = AnnoyIndex(1, metric='euclidean')
for idx in trange(len(indices), desc='annoy index row'):
  t.add_item(indices[idx], [values[idx]])

print 'building annoy index'
t.build(NMB_ANNOY_TREES)

print 'saving annoy index'
t.save(OUTPUT_ANNOY_FILE)
