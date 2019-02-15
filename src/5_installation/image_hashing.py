from hashing_algos.adpwhash import generate_ahash, generate_dhash, generate_phash, generate_whash
from hashing_algos.hist import generate_hist, generate_multi_hist
from hashing_algos.tf import generate_tf
from hashing_algos.image_ratio import generate_image_ratio
from hashing_algos.lines import get_hough_line_vectors
import numpy as np
from tqdm import tqdm

# this variable should be imported from elsewhere
# to make sure we use the same number of bins
HIST_NMB_BINS = 8

def get_all_algo_vectors_for_image(file_path):
  algos_to_func = {
    'ahash': generate_ahash,
    'dhash': generate_dhash,
    'phash': generate_phash,
    'whash': generate_whash,
    'hist': lambda _: generate_hist(_, HIST_NMB_BINS),
    'multi_hist': generate_multi_hist,
    'tf': generate_tf,
    'image_ratio': generate_image_ratio,
    'lines': get_hough_line_vectors
  }

  algo_vectors = dict([(algo, func(file_path)) for algo, func in algos_to_func.items()])
  return algo_vectors

if __name__ == '__main__':
  import sys
  from image_matching import compute_image_distance
  from image_score_weight_adjustment import get_top_img_match_by_weights
  import os

  TEST_DIR = '/Users/greg/Desktop/test-images-for-pure-black-and-white-filter'

  TEST_IMAGES = [
    # almost white
    'af47ced1-0b66-40d9-97bf-3b48761f408f.jpg',
    'bc02f6d5-ac26-4c5b-8ebf-fa1431eb4149.jpg',
    'be5afe0b-3984-4543-8f13-91e6729f873a.jpg',
    'fullred.jpg',
  ]

  # first bin can be any value
  # second bin can up to 0.02
  # all remaining bins should be very very close to 0
  black_image_filter = np.array([[999, 0.02] + [1*10**-5] * (HIST_NMB_BINS - 2)] * 3).flatten()

  # True = filter detected this image
  def filter_response(hist, filter):
    filter_result = filter - hist
    return (filter_result >= 0).all()

  for file_name in tqdm(TEST_IMAGES):
    file_path = os.path.join(TEST_DIR, file_name)
    algo_vectors = get_all_algo_vectors_for_image(file_path)
    img_hist = algo_vectors["hist"]

    print('img_hist', img_hist)

    if filter_response(img_hist, black_image_filter):
      print 'DETECTED BLACK!',file_path
    if filter_response(img_hist, white_image_filter):
      print 'DETECTED WHITE!',file_path

  # img_diff_data = compute_image_distance(algo_vectors, hist_nmb_bins=HIST_NMB_BINS)
  # top_match = get_top_img_match_by_weights(img_diff_data)
  # print('top_match', top_match)
