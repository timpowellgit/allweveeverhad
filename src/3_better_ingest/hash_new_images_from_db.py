from tqdm import tqdm
import os
from annoy import AnnoyIndex
from models import db, Artwork, Image
from hashing_algos.hist import BINNING, generate_hist, generate_multi_hist
from hashing_algos.tf import generate_tf
from hashing_algos.adpwhash import generate_ahash, generate_dhash, generate_phash, generate_whash
from hashing_algos.image_ratio import generate_image_ratio
from hashing_algos.lines import get_hough_line_vectors
import numpy as np
from annoy_recreate import recreate_annoy_index
import sys
from functools import partial

DEBUG_ALLOW_ONLY_COPYING_EXISTING_VECTORS = True

ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']
ANNOY_FILES_BASE_DIR = os.environ['ANNOY_FILES_BASE_DIR']
NEW_ANNOY_FILES_DEST_DIR = os.environ['NEW_ANNOY_FILES_DEST_DIR']

HIST_NMB_ANNOY_TREES = 25
HIST_ANNOY_FILES_SUB_DIR = 'hist_missing_some_items_from_db_due_to_zip_issue'
HIST_METRIC = 'euclidean'

TF_NMB_VECTORS = 2048
TF_NMB_TREES = 1
TF_METRIC = 'euclidean'
TF_ANNOY_FILE_SUB_PATH = 'tf-merged.ann'
TF_GRAPH_PATH = 'tensorflow_inception_classify_image_graph_def.pb'

IMG_HASH_NMB_VECTORS = 64
IMG_HASH_METRIC = 'hamming'
IMG_HASH_ANNOY_FILES_SUB_DIR = 'imagehash'
IMG_HASH_NMB_ANNOY_TREES = 1

IMAGE_RATIO_NMB_VECTORS = 1
IMAGE_RATIO_METRIC = 'euclidean'
IMAGE_RATIO_ANNOY_FILE_SUB_PATH = 'image_ratio.ann'
IMAGE_RATIO_NMB_ANNOY_TREES = 1

# 9 block, 3 channels, 16 bins per channel
MULTI_HIST_NMB_VECTORS = 9 * 3 * 16
MULTI_HIST_METRIC = 'euclidean'
MULTI_HIST_ANNOY_FILE_SUB_PATH = 'multi_hist.ann'
MULTI_HIST_NMB_ANNOY_TREES = 25

LINES_NMB_VECTORS = 10
LINES_METRIC = 'manhattan'
LINES_ANNOY_FILES_SUB_DIR = 'lines'
LINES_NMB_ANNOY_TREES = 20

db.init(ARTWORKS_SQLITE_PATH)

def insert_new_vectors_into_annoy_indices(min_db_id, max_db_id, which_algo):
  # getting all existing image db ids
  # these will be re-copied verbatim into the new annoy indices
  all_db_images_ids = [_[0] for _ in Image.select(Image.id).tuples()]
  print len(all_db_images_ids), 'images in db total'

  db_ids_to_process = [_ for _ in all_db_images_ids if (max_db_id >= _ >= min_db_id)]
  db_ids_to_copy = list(set(all_db_images_ids) - set(db_ids_to_process))

  print 'copying', len(db_ids_to_copy), 'vectors'
  print 'processing', len(db_ids_to_process), 'images'

  if len(db_ids_to_process) == 0 and not DEBUG_ALLOW_ONLY_COPYING_EXISTING_VECTORS:
    print 'no new db ids to process, bailing'
    return

  # TF
  algos = [{
    'name': 'tf',
    'nmb_vectors': TF_NMB_VECTORS,
    'metric': TF_METRIC,
    'annoy_index_path': TF_ANNOY_FILE_SUB_PATH,
    'generate_vector_f': lambda all_ids_to_image_paths: \
                          generate_tf(all_ids_to_image_paths,
                            os.path.join(ANNOY_FILES_BASE_DIR, TF_GRAPH_PATH)),
    'nmb_annoy_trees': TF_NMB_TREES,
    'process_all_images_at_once': True
  }]

  # HIST
  # ONLY DO 8 and 16 from now on!
  # for nmb_bins in BINNING:
  for nmb_bins in [8, 16]:
    annoy_index_path = os.path.join(HIST_ANNOY_FILES_SUB_DIR,
                                    'rgb_hist_{}_bins.ann'.format(nmb_bins))
    algos.append({
      'name': 'hist-{}'.format(nmb_bins),
      'nmb_vectors': nmb_bins * 3,
      'metric': HIST_METRIC,
      'annoy_index_path': annoy_index_path,
      'generate_vector_f': partial(generate_hist, nmb_bins=nmb_bins),
      'nmb_annoy_trees': HIST_NMB_ANNOY_TREES,
    })

  # HASHES
  img_hash_algos = {
    'ahash': generate_ahash,
    'dhash': generate_dhash,
    'phash': generate_phash,
    'whash': generate_whash,
  }
  for hash_algo_name, hash_algo_f in img_hash_algos.items():
    annoy_index_path = os.path.join(IMG_HASH_ANNOY_FILES_SUB_DIR,
                                    'imagehash_{}.ann'.format(hash_algo_name))
    algos.append({
      'name': hash_algo_name,
      'nmb_vectors': IMG_HASH_NMB_VECTORS,
      'metric': IMG_HASH_METRIC,
      'annoy_index_path': annoy_index_path,
      'generate_vector_f': hash_algo_f,
      'nmb_annoy_trees': IMG_HASH_NMB_ANNOY_TREES,
    })
   
  algos.append({
    'name': 'image_ratio',
    'nmb_vectors': IMAGE_RATIO_NMB_VECTORS,
    'metric': IMAGE_RATIO_METRIC,
    'annoy_index_path': IMAGE_RATIO_ANNOY_FILE_SUB_PATH,
    'generate_vector_f': generate_image_ratio,
    'nmb_annoy_trees': IMAGE_RATIO_NMB_ANNOY_TREES
  })

  algos.append({
    'name': 'multi_hist',
    'nmb_vectors': MULTI_HIST_NMB_VECTORS,
    'metric': MULTI_HIST_METRIC,
    'annoy_index_path': MULTI_HIST_ANNOY_FILE_SUB_PATH,
    'generate_vector_f': generate_multi_hist,
    'nmb_annoy_trees': MULTI_HIST_NMB_ANNOY_TREES
  })

  # get paths from db IDs once
  image_ids_to_paths = {}
  for db_index in tqdm(db_ids_to_process, desc='fetching img_local_path'):
    image_ids_to_paths[db_index] = Image.get_by_id(db_index).img_local_path

  # if either of the line algos, do hough line processing (as hough line
  # provides 3 algo results during the same call)
  # only 1 annoy file will be created for the specific chosen algo
  if which_algo in ['all', 'lines_angle', 'lines_horiz_dist', 'lines_vert_dist']:
    # build cache of hough line results (three algo results for the price of one call)
    cached_lined_vector_results_per_image_path = {}
    # process line algo once (not three times!!!) and extract angle/vert/horiz later
    for img_local_path in tqdm(image_ids_to_paths.values(),
                                      desc='apply line algo to local paths'):
      cached_lined_vector_results_per_image_path[img_local_path] = get_hough_line_vectors(img_local_path)

    def get_sub_line_result(sub_line_algo):
      def f(image_path):
        # get result from cache
        res = cached_lined_vector_results_per_image_path[image_path]
        if res is None:
          return None
        return res['{}_hist'.format(sub_line_algo)]
      return f

    for line_algo in ['angle', 'horiz_dist', 'vert_dist']:  
      algos.append({
        'name': 'lines_{}'.format(line_algo),
        'nmb_vectors': LINES_NMB_VECTORS,
        'metric': 'manhattan',
        'annoy_index_path': os.path.join(LINES_ANNOY_FILES_SUB_DIR,
                                          '{}.ann'.format(line_algo)),
        'generate_vector_f': get_sub_line_result(line_algo),
        'nmb_annoy_trees': LINES_NMB_ANNOY_TREES
      })

  if which_algo != 'all':
    algos = filter(lambda a: a['name'] == which_algo, algos)

  for algo in algos:
    print 'applying',algo['name']
   
    new_vectors = {}

    if algo.get('process_all_images_at_once'):
      # special case for TF which is faster when called with all of the image
      # paths at once as tf graph can be loaded once for all (and not once per image)
      new_vectors = algo['generate_vector_f'](
        all_ids_to_image_paths=image_ids_to_paths
      )
    else:
      for db_index, img_local_path in tqdm(image_ids_to_paths.items(), desc='applying algo to db ids'):
        new_vector = algo['generate_vector_f'](
          image_path=img_local_path
        )
        if new_vector is None:
          continue
        new_vectors[db_index] = new_vector
        
    annoy_src_file_path = os.path.join(ANNOY_FILES_BASE_DIR, algo['annoy_index_path'])
    annoy_dest_file_path = os.path.join(NEW_ANNOY_FILES_DEST_DIR, algo['annoy_index_path'])

    # get dirs component of dest annoy file path
    dirs, _ = os.path.split(annoy_dest_file_path)
    # create all necessary dest dirs
    if not os.path.isdir(dirs):
      os.makedirs(dirs)

    recreate_annoy_index(
      nmb_trees=algo['nmb_annoy_trees'],
      nmb_vectors=algo['nmb_vectors'],
      metric=algo['metric'],
      curr_annoy_file_path=annoy_src_file_path,
      new_annoy_file_path=annoy_dest_file_path,
      keep_vector_ids=db_ids_to_copy,
      new_vectors=new_vectors
    )

    print 'recreate_annoy_index done'

if __name__ == '__main__':
  assert len(sys.argv) in [3,4], 'usage: python {} MIN_DB_ID MAX_DB_ID [ALGO]'.format(sys.argv[0])
  min_db_id = int(sys.argv[1])
  max_db_id = int(sys.argv[2])
  which_algo = 'all'
  if len(sys.argv) == 4:
    which_algo = sys.argv[3]
  insert_new_vectors_into_annoy_indices(min_db_id, max_db_id, which_algo)
