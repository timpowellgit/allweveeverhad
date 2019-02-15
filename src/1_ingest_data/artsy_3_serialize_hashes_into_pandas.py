import pickle
from imagehash import hex_to_hash
from tqdm import tqdm
import pandas as pd
from models import db, Image

PICKLE_HASHES_AS_STR_FILE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_hashes.pickle'
PICKLED_PANDAS_DATAFRAME_FILE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_hashes_pandas.pickle'
ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/artworks.sqlite3'

MAX_ROWS_FOR_REDUX_OUTPUT = 1000
DEBUG = False

db.init(ARTWORKS_SQLITE_PATH)


if DEBUG:
  print 'debug debug debug'
  DEBUG_SINGLE_IMG = {'---3C8HsPGPvWinDg0pf8Q': {'source_id': '---3C8HsPGPvWinDg0pf8Q', 'file_path': '/mnt/volume-nyc1-01/artsy-images/d32dm0rphc51dk.cloudfront.net/---3C8HsPGPvWinDg0pf8Q/larger.jpg', 'file_hash_info': {'dhash': 'f2f2f2f2f2f0c9c9', 'ahash': '18383818183c7c7c', 'phash': '8c3cb3623cf2cd4c', 'whash': '1a3a3a18187c7c7f'}},
                      '---3C8HsPGPvWinDgaaaaa': {'source_id': '---3C8HsPGPvWinDgaaaaa', 'file_path': '/mnt/volume-nyc1-01/artsy-images/d32dm0rphc51dk.cloudfront.net/---3C8HsPGPvWinDg0pf8Q/larger.jpg', 'file_hash_info': {'dhash': 'f2f2f2f2f2f0c9c9', 'ahash': '18383818183c7c7c', 'phash': '8c3cb3623cf2cd4c', 'whash': '1a3a3a18187c7c7f'}}}
  all_hashes = DEBUG_SINGLE_IMG
  PICKLED_PANDAS_DATAFRAME_FILE_PATH += '-debug'
else:
  print 'loading pickled hashes'
  with open(PICKLE_HASHES_AS_STR_FILE_PATH) as f:
    all_hashes = pickle.load(f)


df_cols = all_hashes.values()[0]['file_hash_info'].keys()

source_id_index_rows = []
hash_rows_to_numpy = []

print 'process hashes from str to numpy in memory, append to array'
for curr_img_key, curr_img_value in tqdm(all_hashes.items()):
  img_obj = Image.select().where(
    Image.img_local_path == curr_img_value['file_path']).execute()
  assert len(img_obj) == 1
  img_obj = img_obj[0]

  # store row id from db
  source_id_index_rows.append(img_obj.id)

  # extract .hash from imagehash object
  obj = dict([(_[0], hex_to_hash(_[1]).hash) \
                      for _ in curr_img_value['file_hash_info'].items()])

  # build row of values in the same col order as df_cols
  row_values = [obj[col] for col in df_cols]

  hash_rows_to_numpy.append(row_values)

print 'converting to dataframe in one go'
all_df = pd.DataFrame(hash_rows_to_numpy,
                      columns=df_cols,
                      index=source_id_index_rows)

print 'pickling redux data frame'
all_df[:MAX_ROWS_FOR_REDUX_OUTPUT].to_pickle(
  PICKLED_PANDAS_DATAFRAME_FILE_PATH + '-redux')

print 'pickling data frame'
all_df.to_pickle(PICKLED_PANDAS_DATAFRAME_FILE_PATH)
