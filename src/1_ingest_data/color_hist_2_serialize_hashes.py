import os
import pickle
import base64
import numpy as np
import pandas as pd
from tqdm import tqdm

#DIR_OF_PICKLE_FILES = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/histogram-reprocessed-on-all-data-using-range'
DIR_OF_PICKLE_FILES = '/root/color-histogram-processing/histograms-complete'
#PICKLED_PANDAS_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_met_color_hist_pandas.pickle'
PICKLED_PANDAS_FILE = '/root/color-histogram-processing/histograms.pickle-pandas'
#PICKLED_REDUX_PANDAS_FILE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_met_color_hist_pandas.pickle-redux'
PICKLED_REDUX_PANDAS_FILE = '/root/color-histogram-processing/histograms.pickle-pandas-redux'

HISTOGRAM_BINS_LIST = [8,16,32,64,128]

all_pickle_file_data = []

pickle_filepaths = filter(lambda _: _.endswith('.pickle'), os.listdir(DIR_OF_PICKLE_FILES))
for pickle_file_path in tqdm(pickle_filepaths, desc='pickle files'):
  with open(os.path.join(DIR_OF_PICKLE_FILES, pickle_file_path)) as f:
    filesize = os.fstat(f.fileno()).st_size
    tqdm_progress_bar = tqdm(total=filesize, desc='file position')
    last_f_tell = 0
    while True:
      try:
        all_pickle_file_data.append(pickle.load(f))
        tqdm_progress_bar.update(f.tell() - last_f_tell)
        last_f_tell = f.tell()
      except EOFError:
        # pickle file done
        break
    tqdm_progress_bar.close()

print 'loaded {} histograms from pickle data files'.format(len(all_pickle_file_data))

print 'splitting db_indices from hashes using zip*'
# split all 0th element and 1st element into two lists
db_indices, hashes = zip(*all_pickle_file_data)

# make sure we have the same number of columns
# we are not pickling any meta data on columns (their names...!) so the
# remapping from whatever we find in the pickles file to the HISTOGRAM_BINS_LIST
# cols is an 'informed' guess......
# ((these cols come from color_hist_1...py but that file has often evolved))
assert len(HISTOGRAM_BINS_LIST) == len(hashes[0])

print 'creating pandas dataframe'
df = pd.DataFrame(np.array(hashes).tolist(), index=db_indices,
            columns=['rgb_hist_{}_bins'.format(_) for _ in HISTOGRAM_BINS_LIST])

print 'pickling redux dataframe'
df[:1000].to_pickle(PICKLED_REDUX_PANDAS_FILE)

print 'pickling dataframe'
df.to_pickle(PICKLED_PANDAS_FILE)
