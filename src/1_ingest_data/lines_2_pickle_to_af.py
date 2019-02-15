import os
from tqdm import tqdm, trange
import pickle
import numpy as np
from annoy import AnnoyIndex
import operator
import pandas as pd


PICKLE_LINE_FILES_DIR = '/Volumes/Phatty/ART-freeriots-to-make-more-room-on-tw/hough lines pickle'
OUTPUT_ANNOY_FILE_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/annoy_data/lines'

NMB_ANNOY_TREES = 20

# angle, vert dist and horiz dist all use 10 bin hists
# because I didn't change np.histogram's default
NMB_VECTORS = 10

all_data = []

pickle_line_file_names = sorted(filter(lambda _: '.pickle' in _, os.listdir(PICKLE_LINE_FILES_DIR)))

for filename in tqdm(pickle_line_file_names, desc='pickle file'):
  path = os.path.join(PICKLE_LINE_FILES_DIR, filename)
  with open(path) as f:
    filesize = os.fstat(f.fileno()).st_size
    tqdm_progress_bar = tqdm(total=filesize, desc='file position')
    last_f_tell = 0
    while True:
      try:
        data = pickle.load(f)
        if np.all(data[1]['angle_hist'] == 0):
          # no lines detected, skip
          continue
        # image id as key, vector as value
        all_data.append(data)
        tqdm_progress_bar.update(f.tell() - last_f_tell)
        last_f_tell = f.tell()
      except Exception as e:
        print e
        break
    tqdm_progress_bar.close()

print 'read',len(all_data),'lines from pickle files'

for annoy_index in ['angle', 'horiz_dist', 'vert_dist']:
  print 'index: {}'.format(annoy_index)

  index_data = {}
  for key, vectors in all_data:
    # extract angle/horiz/vert
    vector = vectors['{}_hist'.format(annoy_index)]

    if np.all(vector == 0):
      # don't add 0 vectors for either angle, horiz or vert
      continue

    # important to create annoy index that doesn't segfault...!
    vector = vector.astype('float64')

    # build dictionary
    index_data[key] = [vector]

  print 'un-tangling columns using zip'
  indices, values = zip(*[(k, index_data[k]) for k in sorted(index_data)])

  print('len(indices)', len(indices))

  print 'creating data frame'
  df = pd.DataFrame(list(values), index=indices, columns=[annoy_index])

  print 'inserting into annoy index'
  t = AnnoyIndex(NMB_VECTORS, metric='manhattan')
  for idx in trange(len(indices), desc='annoy index row'):
    t.add_item(indices[idx], values[idx][0])

  print 'building annoy index'
  t.build(NMB_ANNOY_TREES)

  print 'saving annoy index'
  t.save(os.path.join(OUTPUT_ANNOY_FILE_DIR, '{}.ann'.format(annoy_index)))
