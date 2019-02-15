from annoy import AnnoyIndex
from models import db, Artwork, Image
from tqdm import tqdm
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
from sklearn import datasets
import numpy as np

DEBUG_MAX_ROWS = 100000

ANNOY_INDEX_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/newer_even_still_annoy_files_allpainters_moma_jf_guido_allpainters_email/tf-merged.ann'
NMB_VECTORS_START = 2048
NMB_VECTORS_END = 1024
NMB_TREES = 1
METRIC = 'euclidean'
RANDOM_STATE = 162954531

ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3'

db.init(ARTWORKS_SQLITE_PATH)

existing_index = AnnoyIndex(NMB_VECTORS_START, metric=METRIC)
existing_index.load(ANNOY_INDEX_PATH)

all_db_images_ids = [_[0] for _ in Image.select(Image.id).tuples()]

existing_index_rows = {}

nmb_un_tf_images = 0
# iterate through annoy rows
for vector_idx_idx, vector_id in enumerate(tqdm(all_db_images_ids, desc='getting all db ids from anoy file')):
  try:
    existing_vector = existing_index.get_item_vector(vector_id)
  except IndexError:
    nmb_un_tf_images += 1
    continue

  assert np.array(existing_vector).dtype == np.float64,\
          'not float64, vector id {}'.format(vector_id)
  assert len(existing_vector) == NMB_VECTORS_START,\
          'len of vector is not nmb_vectors, vector id {}'.format(vector_id)

  existing_index_rows[vector_id] = existing_vector

  if DEBUG_MAX_ROWS:
    if vector_idx_idx == DEBUG_MAX_ROWS:
      break

print('len(existing_index_rows)', len(existing_index_rows))
print('nmb_un_tf_images', nmb_un_tf_images)

# once all annoy data in memory, reduce
###### REDUCE DIMENSIONS #########

existing_index_rows_indices, existing_index_rows_values = zip(*existing_index_rows.items())
existing_index_rows_values = np.array(existing_index_rows_values)
print('existing_index_rows_values.shape', existing_index_rows_values.shape)
# print('existing_index_rows_values', existing_index_rows_values)

print 'Standardize the feature matrix'
X = StandardScaler().fit_transform(existing_index_rows_values)

print 'Make sparse matrix'
X_sparse = csr_matrix(X)

print 'Create a TSVD'
tsvd = TruncatedSVD(n_components=NMB_VECTORS_END, random_state=RANDOM_STATE)

print 'Conduct TSVD on sparse matrix'
X_sparse_tsvd = tsvd.fit(X_sparse)

# store components_
print('X_sparse_tsvd.components_.shape', X_sparse_tsvd.components_.shape)
