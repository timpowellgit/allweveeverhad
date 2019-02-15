from models import db, Artwork, Image
import pickle
from imagehash import hex_to_hash
from tqdm import tqdm
import pandas as pd
from string import strip
import codecs

FILEPATHS_AND_HASHES_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/MET/metmuseum-images-hashes-the-actual-hashes.txt'
PICKLED_PANDAS_DATAFRAME_FILE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/met_hashes_panda.pickle'
ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/artworks.sqlite3'

db.init(ARTWORKS_SQLITE_PATH)

row_indices = []
hash_rows_to_numpy = []

artworks_not_in_db = 0

print 'loading FILEPATHS_AND_HASHES_PATH'
with codecs.open(FILEPATHS_AND_HASHES_PATH, 'r', encoding='latin-1') as f:
  all_filepaths_and_hashes = f.readlines()

# header line
algo_col_names = all_filepaths_and_hashes[0].strip().split(',')[1:]
for line in tqdm(all_filepaths_and_hashes[1:]):
  line = line.strip()

  # up to as-many-algos
  # this is necessary since filepaths can contain spaces
  filepath = ' '.join(line.split(' ')[:-len(algo_col_names)])
  hash_values = line.split(' ')[-len(algo_col_names):]

  if len(hash_values) != len(algo_col_names):
    print 'ERR',line
    continue

  res = Image.select().where(Image.img_local_path == filepath).execute()

  if len(res) == 0:
    artworks_not_in_db += 1
    continue

  assert len(res) == 1,\
    ('ERR in query',filepath,line)

  # store id of Image table row as pandas index
  row_indices.append(res[0].id)

  hash_values = [hex_to_hash(_).hash for _ in hash_values]
  hash_rows_to_numpy.append(hash_values)

print('artworks_not_in_db', artworks_not_in_db)

print 'converting to dataframe in one go'
all_df = pd.DataFrame(hash_rows_to_numpy,
                      columns=algo_col_names,
                      index=row_indices)

print 'pickling data frame'
all_df.to_pickle(PICKLED_PANDAS_DATAFRAME_FILE_PATH)
