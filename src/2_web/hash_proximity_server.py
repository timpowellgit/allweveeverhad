import pickle
import pandas as pd
from flask import Flask, request, jsonify
from imagehash import hex_to_hash
import numpy as np
import os
import base64
import scipy
from scipy import spatial
from annoy import AnnoyIndex

DEBUG = 'true'#os.environ['HASH_PROXIM_SERVER_DEBUG'] == 'true'

DEBUG_RUN_TF_ALGO = False
DEBUG_RUN_HIST_ALGO = True
DEBUG_RUN_MULTI_HIST_ALGO = False
DEBUG_RUN_LINES_ALGO = False
DEBUG_RUN_HASHING_ALGOS = False
DEBUG_RUN_IMAGE_RATIO_ALGO = True

FLASK_HOST = "127.0.0.1"#os.environ['HASH_PROXIM_SERVER_FLASK_HOST']
FLASK_DEBUG = 'true' #os.environ['HASH_PROXIM_SERVER_FLASK_DEBUG'] == 'true'

# pandas terminal output options to use full terminal width
pd.set_option('display.large_repr', 'truncate')
pd.set_option('display.max_columns', 0)

PORT = 9999 #int(os.environ['HASH_PROXIM_SERVER_FLASK_PORT'])

# --------

REALTIME_PICKLE_DIFF_PATH_OUT = '/Users/timothypowell/allweveeverhad-master/pickle_toss/last_diff_results_for_realtime.pickle'#os.environ['REALTIME_PICKLE_DIFF_PATH_OUT']

# --------

ANNOY_FILES_BASE_DIR = '/Users/timothypowell/allweveeverhad-master/serialized_data/newer_even_still_annoy_files_allpainters_moma_jf_guido_allpainters_email' #os.environ['ANNOY_FILES_BASE_DIR']

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

MAX_HASH_ROWS_TO_RETURN = 100
MAX_HIST_ROWS_TO_RETURN = 100
MAX_HIST_ROWS_TO_USE_FOR_PIPELINE_ALGOS = 10000
MAX_TF_ROWS_TO_RETURN = 100
MAX_IMAGE_RATIO_ROWS_TO_RETURN = 100
MAX_MULTI_HIST_ROWS_TO_RETURN = 100
MAX_LINES_ROWS_TO_RETURN = 100

# defaults when none provided by main server (which should not happen...)
MAX_DISTANCE_ADPW_HASH = 8
MAX_DISTANCE_HISTOGRAM = 0.2
MAX_DISTANCE_TF = 20
MAX_DISTANCE_IMAGE_RATIO = 0.3
MAX_DISTANCE_MULTI_HIST = 0.1
MAX_DISTANCE_LINES_ANGLE = 0.1
MAX_DISTANCE_LINES_VERT_DIST = 0.1
MAX_DISTANCE_LINES_HORIZ_DIST = 0.1


# --------

def b64_decode(s):
  r = base64.decodestring(s)
  return np.frombuffer(r, dtype=np.float64)

print 'starting Flask'
app = Flask(__name__)

@app.route("/", methods=['POST'])
# @profile
def hash_distance():
  # only accepts POST now

  # URL args (any of):
  # ahash, dhash, phash, whash
  ## optional:
  # max_distance_adpw_hash (default: 8)

  # POST args:
  # histogram
  ## optional:
  # max_distance_histogram (default: 0.1)
  # nmb_histogram_bins (one of [8,16,32,64,128])
  # ---
  # tf
  ## optional:
  # max_distance_tf (default: 20)
  # ---
  # src_image_ratio
  # max_distance_image_ratio (default: 0.3)
  # ---
  # base64_encoded_multi_hist
  # max_distance_multi_hist (default: 0.1)

  # key is hash algo, each value is dict of src_id:delta
  out_results = {}

  # copied diff rows for synthetic histogram -> hashing algo
  selected_histogram_rows = None

  diff_cols_for_realtime_calibration = []

  if DEBUG_RUN_TF_ALGO and 'tf' in request.form:
    max_distance_tf = MAX_DISTANCE_TF
    if 'max_distance_tf' in request.form:
      max_distance_tf = float(request.form['max_distance_tf'])

    needle_tf = b64_decode(request.form['tf'])
    # tf has 2048 vectors
    annoy_index = AnnoyIndex(2048, metric='euclidean')
    annoy_index.load(os.path.join(
      ANNOY_FILES_BASE_DIR,
      TF_ANNOY_FILE_SUB_PATH
    ))

    # get_nns_by_vector returns results sorted by distance asc
    print "Getting tensor flow nearest neighbors"
    sorted_tf_dist = annoy_index.get_nns_by_vector(needle_tf,
      TF_MAX_N_FROM_ANNOY,
      search_k=TF_NMB_ANNOY_TREES * 1000 * TF_SEARCH_K_FACTOR,
      include_distances=True)
    annoy_index.unload()

    sorted_tf_delta_df = pd.DataFrame(sorted_tf_dist[1],
                                    index=sorted_tf_dist[0], columns=['dist'])
    diff_cols_for_realtime_calibration.append(sorted_tf_delta_df.rename(columns={'dist': 'tf'}))

    sorted_tf_df_filtered = sorted_tf_delta_df[
                          sorted_tf_delta_df['dist'] < max_distance_tf]
    sorted_tf_df_filtered = sorted_tf_df_filtered['dist']
    # return top MAX_TF_ROWS_TO_RETURN (100 right now) rows to front end
    sorted_tf_df_filtered = sorted_tf_df_filtered[:MAX_TF_ROWS_TO_RETURN]
    out_results['tf'] = sorted_tf_df_filtered.to_dict()

  if DEBUG_RUN_HIST_ALGO and 'histogram' in request.form:
    max_distance_histogram = MAX_DISTANCE_HISTOGRAM
    if 'max_distance_histogram' in request.form:
      max_distance_histogram = float(request.form['max_distance_histogram'])

    histogram_col = 'rgb_hist_{}_bins'.format(request.form['nmb_histogram_bins'])

    needle_histogram = b64_decode(request.form['histogram'])

    # nmb of vectors in annoy file is nmb_bins * 3 channels
    nmb_vectors = int(request.form['nmb_histogram_bins']) * 3
    annoy_index = AnnoyIndex(nmb_vectors, metric='euclidean')
    annoy_index_path = os.path.join(
            ANNOY_FILES_BASE_DIR,
            HISTOGRAM_ANNOY_FILES_SUB_DIR,
            '{}.ann'.format(histogram_col))
    annoy_index.load(annoy_index_path)
    print "Getting histogram nearest neighbors"

    # get_nns_by_vector returns results sorted by distance asc
    sorted_color_hist_dist = annoy_index.get_nns_by_vector(needle_histogram,
      HISTOGRAM_MAX_N_FROM_ANNOY,
      search_k=HISTOGRAM_NMB_ANNOY_TREES * 1000 * HISTOGRAM_SEARCH_K_FACTOR,
      include_distances=True)
    annoy_index.unload()

    sorted_hist_delta_df = pd.DataFrame(sorted_color_hist_dist[1],
                                    index=sorted_color_hist_dist[0], columns=['dist'])

    diff_cols_for_realtime_calibration.append(sorted_hist_delta_df.rename(columns={'dist': 'hist'}))

    sorted_hist_df_filtered = sorted_hist_delta_df[
                          sorted_hist_delta_df['dist'] < max_distance_histogram]
    sorted_hist_df_filtered = sorted_hist_df_filtered['dist']

    # 'copy' selected histogram rows according to
    # - "special" max hist result rows to re-use for pipeline/synthetic/mulit-step algos
    #   (1000 right now)
    # - max_distance_histogram
    selected_histogram_rows = sorted_hist_df_filtered[:MAX_HIST_ROWS_TO_USE_FOR_PIPELINE_ALGOS]

    # return top MAX_HIST_ROWS_TO_RETURN (100 right now) rows to front end
    sorted_hist_df_filtered = sorted_hist_df_filtered[:MAX_HIST_ROWS_TO_RETURN]
    out_results['histogram'] = sorted_hist_df_filtered.to_dict()

  if DEBUG_RUN_IMAGE_RATIO_ALGO and 'src_image_ratio' in request.form:
    max_distance_image_ratio = MAX_DISTANCE_IMAGE_RATIO
    if 'max_distance_image_ratio' in request.form:
      max_distance_image_ratio = float(request.form['max_distance_image_ratio'])
    src_image_ratio_vector = [float(request.form['src_image_ratio'])]

    nmb_vectors = 1
    annoy_index = AnnoyIndex(nmb_vectors, metric='euclidean')
    annoy_index.load(os.path.join(
      ANNOY_FILES_BASE_DIR,
      IMAGE_RATIO_ANNOY_FILE_SUB_PATH
    ))
    print "Getting image ratio nearest neighbors"

    sorted_image_ratio_dist = annoy_index.get_nns_by_vector(src_image_ratio_vector,
      # annoy index is fragile with vectors of length 1
      # don't query more than 10k results
      10000,
      include_distances=True)
    annoy_index.unload()

    sorted_image_ratio_delta_df = pd.DataFrame(sorted_image_ratio_dist[1],
      index=sorted_image_ratio_dist[0], columns=['dist'])

    diff_cols_for_realtime_calibration.append(sorted_image_ratio_delta_df.rename(columns={
      'dist': 'image_ratio'
    }))

    sorted_image_ratio_df_filtered = sorted_image_ratio_delta_df[
      sorted_image_ratio_delta_df['dist'] < max_distance_image_ratio]
    sorted_image_ratio_df_filtered = sorted_image_ratio_df_filtered['dist']
    # return top MAX_IMAGE_RATIO_ROWS_TO_RETURN rows to frontend
    sorted_image_ratio_df_filtered = sorted_image_ratio_df_filtered[:MAX_IMAGE_RATIO_ROWS_TO_RETURN]
    out_results['image_ratio'] = sorted_image_ratio_df_filtered.to_dict()

  if DEBUG_RUN_MULTI_HIST_ALGO and 'base64_encoded_multi_hist' in request.form:
    max_distance_multi_hist = MAX_DISTANCE_MULTI_HIST
    if 'max_distance_multi_hist' in request.form:
      max_distance_multi_hist = float(request.form['max_distance_multi_hist'])

    needle_multi_hist = b64_decode(request.form['base64_encoded_multi_hist'])

    # 9 blocks, 3 channels per block, 16 hist bins per channel
    nmb_vectors = 9 * 3 * 16
    annoy_index = AnnoyIndex(nmb_vectors, metric='euclidean')
    annoy_index.load(os.path.join(
      ANNOY_FILES_BASE_DIR,
      MULTI_HIST_ANNOY_FILE_SUB_PATH
    ))
    print "Getting multi histogram nearest neighbors"

    sorted_multi_hist_dist = annoy_index.get_nns_by_vector(needle_multi_hist,
      MULTI_HIST_MAX_N_FROM_ANNOY,
      search_k=MULTI_HIST_NMB_ANNOY_TREES * 1000 * MULTI_HIST_SEARCH_K_FACTOR,
      include_distances=True)
    annoy_index.unload()

    sorted_multi_hist_delta_df = pd.DataFrame(sorted_multi_hist_dist[1],
                                    index=sorted_multi_hist_dist[0], columns=['dist'])

    diff_cols_for_realtime_calibration.append(sorted_multi_hist_delta_df.rename(columns={'dist': 'multi_hist'}))

    sorted_multi_hist_df_filtered = sorted_multi_hist_delta_df[
                          sorted_multi_hist_delta_df['dist'] < max_distance_multi_hist]
    sorted_multi_hist_df_filtered = sorted_multi_hist_df_filtered['dist']

    sorted_multi_hist_df_filtered = sorted_multi_hist_df_filtered[:MAX_MULTI_HIST_ROWS_TO_RETURN]
    out_results['multi_hist'] = sorted_multi_hist_df_filtered.to_dict()

  if DEBUG_RUN_LINES_ALGO and 'b64_lines_angle_hist' in request.form:
    nmb_vectors = 10

    line_hists_maxs = [
      ('lines_angle_hist', 'b64_lines_angle_hist', 'max_distance_lines_angle', MAX_DISTANCE_LINES_ANGLE, 'angle.ann'),
      ('lines_vert_dist_hist', 'b64_lines_vert_dist_hist', 'max_distance_lines_vert_dist', MAX_DISTANCE_LINES_VERT_DIST, 'vert_dist.ann'),
      ('lines_horiz_dist_hist', 'b64_lines_horiz_dist_hist', 'max_distance_lines_horiz_dist', MAX_DISTANCE_LINES_HORIZ_DIST, 'horiz_dist.ann'),
    ]

    for curr_hist_name, curr_hist, curr_max, default_max, annoy_file_path in line_hists_maxs:
      # no information (for either vert or horiz)
      if curr_hist not in request.form:
        continue

      curr_hist = b64_decode(request.form[curr_hist])

      if curr_max in request.form:
        curr_max = float(request.form[curr_max])
      else:
        curr_max = default_max

      # using manhattan because of specific issue with this index /
      # using non sequentials IDs and euclidean distance
      # (as reported to annoy project -- see below)
      annoy_index = AnnoyIndex(nmb_vectors, metric='manhattan')
      annoy_full_file_path = os.path.join(
        ANNOY_FILES_BASE_DIR,
        LINES_ANNOY_DIR_SUB_DIR,
        annoy_file_path)
      annoy_index.load(annoy_full_file_path)

      #### BELOW WAS ONLY TRUE WHEN ANNOY VERSION WAS < ...15
      # we've seen segfault issues when using non sequential IDs (as we do)
      # and the euclidean distance:
      # https://github.com/spotify/annoy/issues/288
      # manhattan distance works perfectly for the lines index
      # the only issue is that we've seen at least once
      # the index 0 being returned when it was not used originally when
      # inserting values.
      # will need to double check returned indices before using them
      print "Getting lines nearest neighbors"
      sorted_lines_dist = annoy_index.get_nns_by_vector(curr_hist,
        LINES_MAX_N_FROM_ANNOY,
        search_k=LINES_NMB_ANNOY_TREES * 1000 * LINES_SEARCH_K_FACTOR,
        include_distances=True)
      annoy_index.unload()

      sorted_lines_delta_df = pd.DataFrame(sorted_lines_dist[1],
                                      index=sorted_lines_dist[0], columns=['dist'])

      diff_cols_for_realtime_calibration.append(sorted_lines_delta_df.rename(
        columns={'dist': curr_hist_name}))

      sorted_lines_df_filtered = sorted_lines_delta_df[
                            sorted_lines_delta_df['dist'] < curr_max]
      sorted_lines_df_filtered = sorted_lines_df_filtered['dist']

      sorted_lines_df_filtered = sorted_lines_df_filtered[:MAX_LINES_ROWS_TO_RETURN]
      out_results[curr_hist_name] = sorted_lines_df_filtered.to_dict()

  if DEBUG_RUN_HASHING_ALGOS:
    image_hash_algos = filter(lambda h: h in ['ahash', 'phash', 'dhash', 'whash'],
                              list(request.args))

    image_hash_algo_values = {}
    for algo in image_hash_algos:
      hex_str_value = request.args.get(algo)
      hash_obj = hex_to_hash(hex_str_value)
      hash_flat = hash_obj.hash.flatten()
      image_hash_algo_values[algo] = hash_flat

    max_distance_adpw_hash = request.args.get('max_distance_adpw_hash',
                                              MAX_DISTANCE_ADPW_HASH, type=int)

    for src_hash_algo, src_hash_value in image_hash_algo_values.items():
      annoy_index = AnnoyIndex(64, metric='hamming')
      annoy_index_path = os.path.join(
        ANNOY_FILES_BASE_DIR,
        HASHES_ANNOY_FILES_SUB_DIR,
        'imagehash_{}.ann'.format(src_hash_algo))
      annoy_index.load(annoy_index_path)
      # extracting distance to ALL vectors, even though we should only get 100/1000
      # doing this because we will be extracting indices from this series found by hist
      # match for the hist->hash pipeline
      print "Getting %s nearest neighbors" %(src_hash_algo)
      sorted_hashes_dist = annoy_index.get_nns_by_vector(src_hash_value,
        HASHES_MAX_N_FROM_ANNOY,
        # TODO check -- no search_k...??
        include_distances=True)
      annoy_index.unload()
      
      # pandas series contains delta values for whole dataset
      hash_delta_series = pd.Series(sorted_hashes_dist[1],
                                  index=sorted_hashes_dist[0])

      diff_cols_for_realtime_calibration.append(
        pd.DataFrame(hash_delta_series, columns=[src_hash_algo]))

      sorted_found_rows = hash_delta_series[hash_delta_series <= max_distance_adpw_hash]
      out_results[src_hash_algo] = sorted_found_rows[:MAX_HASH_ROWS_TO_RETURN].to_dict()

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
      diff_cols_for_realtime_calibration.append(
        pd.DataFrame(hash_delta_series_filtered_by_hist, columns=[algo_name]))    

      # append synthetic (pipeline-type) 'algo' results
      out_results[algo_name] = hash_delta_series_filtered_by_hist[:MAX_HASH_ROWS_TO_RETURN].to_dict()

  if len(diff_cols_for_realtime_calibration):
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
    diff_cols_for_realtime_calibration = diff_cols_for_realtime_calibration[0].join(diff_cols_for_realtime_calibration[1:], how='outer')
    # overwrite any existing file
    with open(REALTIME_PICKLE_DIFF_PATH_OUT, 'w') as f:
      pickle.dump(diff_cols_for_realtime_calibration, f)

  return jsonify(out_results)

if __name__ == '__main__':
  # use_reloader=False necessary to use line_profiler
  app.run(host=FLASK_HOST, debug=FLASK_DEBUG, port=PORT, use_reloader=True)
