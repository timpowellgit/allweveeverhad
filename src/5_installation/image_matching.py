import pickle
import pandas as pd
from imagehash import hex_to_hash
import numpy as np
import os
import scipy
from scipy import spatial
from annoy import AnnoyIndex
from tqdm import tqdm
from image_hashing import HIST_NMB_BINS

DEBUG_RUN_TF = True
DEBUG_RUN_HIST = True
DEBUG_RUN_IMAGE_RATIO = True
DEBUG_RUN_MULTI_HIST = True
DEBUG_RUN_LINES = True
DEBUG_RUN_IMGHASHING = True

# ----------------------

ANNOY_FILES_BASE_DIR = os.environ['ANNOY_FILES_BASE_DIR']

# using MAX_NNS for max number of returned rows by annoy is dirty hack:
# no way to tell annoy to return distance to all vectors
# not using get_n_items() to get total number of items in index
# just in case, as I've read reports that it might
# be incorrect, especially for our situation of possibly non-sequential ids
# (ids are possibly not sequential as they are db ids)

# the above having been said, this number was brought down to 9000 because it
# was faster to generate smaller pickle output files.... however...........
# after checking index of 'winners' (post realtime midi knob weighting,
# "winning" results (top 20) were found as indices at positions 1k, 3k, 4k and
# even 8k) this means that some results would have been displayed if it hadn't
# been for the arbritrary 9k number of results being pickled for real time analysis

# will probably increase 9000 number and try to profile this file to see how to
# speed up processing

# profiling only told us that annoy call is by far the longest (with tf taking up 50%
# of the processing time)
# tentatively increasing from 9k to 10k results
# and leaving search_k in (removing it led to speed up but results were subjectively worse)

# having made this number very very small (10k) and having had the wrong join call
# from the beginning, the resulting pickle file had very little information left
# the trick for realtime midi is to actually get all of the distance values and do the weights
# against those... otherwise, you get a very small subset of the best matched images by each algo
# but don't (usually) get diff scores from multiple algos for the same image..... which is a problem
# re-setting this to huge value again in order for the written real time calibration pickle files
# to have everything.......
MAX_NNS = 999999999

HASHES_ANNOY_FILES_SUB_DIR = 'imagehash'
HASHES_MAX_N_FROM_ANNOY = MAX_NNS

HISTOGRAM_ANNOY_FILES_SUB_DIR = 'hist_missing_some_items_from_db_due_to_zip_issue'
HISTOGRAM_MAX_N_FROM_ANNOY = MAX_NNS
HISTOGRAM_SEARCH_K_FACTOR = 10000
HISTOGRAM_NMB_ANNOY_TREES = 25

TF_ANNOY_FILE_SUB_PATH = 'tf-merged.ann'
# TODO use MAX_NNS instead of other max because of issues with annoy and
# non sequential ids??
TF_MAX_N_FROM_ANNOY = MAX_NNS
TF_SEARCH_K_FACTOR = 10000
TF_NMB_ANNOY_TREES = 1

IMAGE_RATIO_ANNOY_FILE_SUB_PATH = 'image_ratio.ann'
# annoy will seg fault if request number of results is greater than number
# of items in index..!
IMAGE_RATIO_MAX_N_FROM_ANNOY = 10000
IMAGE_RATIO_ANNOY_TREES = 1

MULTI_HIST_ANNOY_FILE_SUB_PATH = 'multi_hist.ann'
MULTI_HIST_MAX_N_FROM_ANNOY = MAX_NNS
MULTI_HIST_SEARCH_K_FACTOR = 10000
MULTI_HIST_NMB_ANNOY_TREES = 25

LINES_ANNOY_DIR_SUB_DIR = 'lines'
LINES_MAX_N_FROM_ANNOY = MAX_NNS
LINES_NMB_ANNOY_TREES = 20
LINES_SEARCH_K_FACTOR = 10000

MAX_HIST_ROWS_TO_USE_FOR_PIPELINE_ALGOS = 10000
MAX_HIST_DISTANCE_FOR_PIPELINE = 0.2

# --------

annoy_indices = {}
# LOAD ALL THE ANNOY FILES INTO MEMORY AND NEVER UNLOAD THEM EVER
with tqdm(total=6, desc='loading annoy indices') as pbar:
  # tf has 2048 vectors
  annoy_indices['tf'] = AnnoyIndex(2048, metric='euclidean')
  annoy_indices['tf'].load(os.path.join(
    ANNOY_FILES_BASE_DIR,
    TF_ANNOY_FILE_SUB_PATH
  ))
  pbar.update(1)

  histogram_col = 'rgb_hist_{}_bins'.format(HIST_NMB_BINS)
  # nmb of vectors in annoy file is nmb_bins * 3 channels
  nmb_vectors = HIST_NMB_BINS * 3
  annoy_indices['hist'] = AnnoyIndex(nmb_vectors, metric='euclidean')
  annoy_index_path = os.path.join(
          ANNOY_FILES_BASE_DIR,
          HISTOGRAM_ANNOY_FILES_SUB_DIR,
          '{}.ann'.format(histogram_col))
  annoy_indices['hist'].load(annoy_index_path)
  pbar.update(1)

  nmb_vectors = 1
  annoy_indices['image_ratio'] = AnnoyIndex(nmb_vectors, metric='euclidean')
  annoy_indices['image_ratio'].load(os.path.join(
    ANNOY_FILES_BASE_DIR,
    IMAGE_RATIO_ANNOY_FILE_SUB_PATH
  ))
  pbar.update(1)

  # 9 blocks, 3 channels per block, 16 hist bins per channel
  nmb_vectors = 9 * 3 * 16
  annoy_indices['multi_hist'] = AnnoyIndex(nmb_vectors, metric='euclidean')
  annoy_indices['multi_hist'].load(os.path.join(
    ANNOY_FILES_BASE_DIR,
    MULTI_HIST_ANNOY_FILE_SUB_PATH
  ))
  pbar.update(1)

  # using manhattan because of specific issue with this index /
  # using non sequentials IDs and euclidean distance
  # (as reported to annoy project -- see below)
  nmb_vectors = 10
  for line_annoy_file_name in ['angle.ann', 'vert_dist.ann', 'horiz_dist.ann']:
    annoy_indices[line_annoy_file_name] = AnnoyIndex(nmb_vectors, metric='manhattan')
    annoy_full_file_path = os.path.join(
      ANNOY_FILES_BASE_DIR,
      LINES_ANNOY_DIR_SUB_DIR,
      line_annoy_file_name)
    annoy_indices[line_annoy_file_name].load(annoy_full_file_path)
  pbar.update(1)

  image_algo_names = ['ahash', 'phash', 'dhash', 'whash']
  for image_algo_name in image_algo_names:
    annoy_indices[image_algo_name] = AnnoyIndex(64, metric='hamming')
    annoy_index_path = os.path.join(
      ANNOY_FILES_BASE_DIR,
      HASHES_ANNOY_FILES_SUB_DIR,
      'imagehash_{}.ann'.format(image_algo_name))
    annoy_indices[image_algo_name].load(annoy_index_path)
  pbar.update(1)


def compute_image_distance(algo_vectors, hist_nmb_bins):
  # 6 algos total
  pbar = tqdm(total=6, desc='image distance algos')

  output_for_weights_mult_scoring = []

  # copied diff rows for synthetic histogram -> hashing algo
  selected_histogram_rows = None

  ############ TF
  if DEBUG_RUN_TF:
    pbar.update(1)

    needle_tf = algo_vectors['tf']

    # get_nns_by_vector returns results sorted by distance asc
    sorted_tf_dist = annoy_indices['tf'].get_nns_by_vector(needle_tf,
      TF_MAX_N_FROM_ANNOY,
      search_k=TF_NMB_ANNOY_TREES * 1000 * TF_SEARCH_K_FACTOR,
      include_distances=True)

    sorted_tf_delta_df = pd.DataFrame(sorted_tf_dist[1],
                                    index=sorted_tf_dist[0], columns=['dist'])

    output_for_weights_mult_scoring.append(sorted_tf_delta_df.rename(columns={'dist': 'tf'}))

  #################### HIST
  if DEBUG_RUN_HIST:
    pbar.update(1)

    needle_histogram = algo_vectors['hist']

    # get_nns_by_vector returns results sorted by distance asc
    sorted_color_hist_dist = annoy_indices['hist'].get_nns_by_vector(needle_histogram,
      HISTOGRAM_MAX_N_FROM_ANNOY,
      search_k=HISTOGRAM_NMB_ANNOY_TREES * 1000 * HISTOGRAM_SEARCH_K_FACTOR,
      include_distances=True)

    sorted_hist_delta_df = pd.DataFrame(sorted_color_hist_dist[1],
                                    index=sorted_color_hist_dist[0], columns=['dist'])

    output_for_weights_mult_scoring.append(sorted_hist_delta_df.rename(columns={'dist': 'hist'}))

    sorted_hist_df_filtered = sorted_hist_delta_df[
                          sorted_hist_delta_df['dist'] < MAX_HIST_DISTANCE_FOR_PIPELINE]
    sorted_hist_df_filtered = sorted_hist_df_filtered['dist']

    # 'copy' selected histogram rows according to
    # - "special" max hist result rows to re-use for pipeline/synthetic/mulit-step algos
    #   (1000 right now)
    # - max_distance_histogram
    selected_histogram_rows = sorted_hist_df_filtered[:MAX_HIST_ROWS_TO_USE_FOR_PIPELINE_ALGOS]

  ############# IMAGE RATIO
  if DEBUG_RUN_IMAGE_RATIO:
    pbar.update(1)

    src_image_ratio_vector = algo_vectors['image_ratio']

    sorted_image_ratio_dist = annoy_indices['image_ratio'].get_nns_by_vector(src_image_ratio_vector,
      # annoy index is fragile with vectors of length 1
      # don't query more than 10k results
      10000,
      include_distances=True)

    sorted_image_ratio_delta_df = pd.DataFrame(sorted_image_ratio_dist[1],
      index=sorted_image_ratio_dist[0], columns=['dist'])

    output_for_weights_mult_scoring.append(sorted_image_ratio_delta_df.rename(columns={
      'dist': 'image_ratio'
    }))

  ##################### MULTI HIST
  if DEBUG_RUN_MULTI_HIST:
    pbar.update(1)

    needle_multi_hist = algo_vectors['multi_hist']

    sorted_multi_hist_dist = annoy_indices['multi_hist'].get_nns_by_vector(needle_multi_hist,
      MULTI_HIST_MAX_N_FROM_ANNOY,
      search_k=MULTI_HIST_NMB_ANNOY_TREES * 1000 * MULTI_HIST_SEARCH_K_FACTOR,
      include_distances=True)

    sorted_multi_hist_delta_df = pd.DataFrame(sorted_multi_hist_dist[1],
                                    index=sorted_multi_hist_dist[0], columns=['dist'])

    output_for_weights_mult_scoring.append(sorted_multi_hist_delta_df.rename(columns={'dist': 'multi_hist'}))

  ######################## LINES
  if DEBUG_RUN_LINES:
    pbar.update(1)

    # there may be no line information! skip it!
    if algo_vectors['lines']:
      line_hists_maxs = [
        ('lines_angle_hist', 'angle_hist', 'angle.ann'),
        ('lines_vert_dist_hist', 'vert_dist_hist', 'vert_dist.ann'),
        ('lines_horiz_dist_hist', 'horiz_dist_hist', 'horiz_dist.ann'),
      ]

      for curr_hist_name, curr_hist, annoy_file_path in line_hists_maxs:
        # no information (for either vert or horiz)
        if curr_hist not in algo_vectors['lines']:
          continue

        curr_hist = algo_vectors['lines'][curr_hist]

        #### BELOW WAS ONLY TRUE WHEN ANNOY VERSION WAS < ...15
        # we've seen segfault issues when using non sequential IDs (as we do)
        # and the euclidean distance:
        # https://github.com/spotify/annoy/issues/288
        # manhattan distance works perfectly for the lines index
        # the only issue is that we've seen at least once
        # the index 0 being returned when it was not used originally when
        # inserting values.
        # will need to double check returned indices before using them
        sorted_lines_dist = annoy_indices[annoy_file_path].get_nns_by_vector(curr_hist,
          LINES_MAX_N_FROM_ANNOY,
          search_k=LINES_NMB_ANNOY_TREES * 1000 * LINES_SEARCH_K_FACTOR,
          include_distances=True)

        sorted_lines_delta_df = pd.DataFrame(sorted_lines_dist[1],
                                        index=sorted_lines_dist[0], columns=['dist'])

        output_for_weights_mult_scoring.append(sorted_lines_delta_df.rename(
          columns={'dist': curr_hist_name}))

  ######################### HASHING ALGOS
  if DEBUG_RUN_IMGHASHING:
    pbar.update(1)

    image_hash_algos = [_ for _ in algo_vectors if _ in ['ahash', 'phash', 'dhash', 'whash']]

    image_hash_algo_values = {}
    for algo in image_hash_algos:
      hash_flat = algo_vectors[algo].flatten()
      image_hash_algo_values[algo] = hash_flat

    for src_hash_algo, src_hash_value in image_hash_algo_values.items():
      # extracting distance to ALL vectors, even though we should only get 100/1000
      # doing this because we will be extracting indices from this series found by hist
      # match for the hist->hash pipeline
      sorted_hashes_dist = annoy_indices[src_hash_algo].get_nns_by_vector(src_hash_value,
        HASHES_MAX_N_FROM_ANNOY,
        # TODO check -- no search_k...??
        include_distances=True)
      
      # pandas series contains delta values for whole dataset
      hash_delta_series = pd.Series(sorted_hashes_dist[1],
                                  index=sorted_hashes_dist[0])

      output_for_weights_mult_scoring.append(
        pd.DataFrame(hash_delta_series, columns=[src_hash_algo]))

      # ------------------------------------------
      # find hash matches within histogram matches

      if selected_histogram_rows is None or not len(selected_histogram_rows):
        continue

      # only pick hash delta values for those rows pickled by histogram
      hash_delta_series_filtered_by_hist = hash_delta_series[selected_histogram_rows.index]
      # normalize hash distances
      hash_delta_series_filtered_by_hist /= 64.0
      # multiply normalized hash distances by histogram distance
      hash_delta_series_filtered_by_hist *= selected_histogram_rows[hash_delta_series_filtered_by_hist.index]

      algo_name = 'hist_{}'.format(src_hash_algo)
      output_for_weights_mult_scoring.append(
        pd.DataFrame(hash_delta_series_filtered_by_hist, columns=[algo_name]))    

  # pandas merging
  # OUTER JOIN!!!!!!! OUTER!!!!!!!!!!!!!
  # not doing outer join means that only the element [0]'s indices will be used
  # to find corresponding indices in other elements added to the array, making
  # all other algos pseudo-post-process-algos to the algo whose results are stored in [0].
  # i.e. if tf results are in [0], a non-outer join will only store/join results from [1, ...]
  # for thos indices for which tf gave a score, making the tf indices a "hard" filter.
  # an outer join will keep all indices -- all unique indices of images for which only
  # one algo returned a value, and for those db indices/images which were chosen by multiple
  # algos and for which scores exist for many algos.
  output_for_weights_mult_scoring = output_for_weights_mult_scoring[0].join(
                                      output_for_weights_mult_scoring[1:], how='outer')

  pbar.close()

  return output_for_weights_mult_scoring
