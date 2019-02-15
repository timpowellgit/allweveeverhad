from flask import Flask, request, redirect, render_template
import requests
import urllib
import imagehash
import PIL
import operator
from collections import OrderedDict
import os
from models import db, Artwork, Image
from collections import Counter
import operator
from scipy import misc
import numpy as np
from itertools import chain
import base64
from tensorflow_classify_image import run_inference_on_image_data
from lines import get_hough_line_vectors

FLASK_HOST = os.environ['WEB_MAIN_FLASK_HOST']
FLASK_PORT = int(os.environ['WEB_MAIN_FLASK_PORT'])
FLASK_DEBUG = os.environ['WEB_MAIN_FLASK_DEBUG'] == 'true'

IMAGE_HASHING_WEB_SERVER = os.environ['IMAGE_HASHING_WEB_SERVER']

ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']

# used for both hist and multi hist
HIST_USE_DENSITY = True

MULTI_HIST_NMB_BINS = 16


db.init(ARTWORKS_SQLITE_PATH)

print 'starting Flask'
app = Flask(__name__)
# set max upload size to 16Mb
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


# ONLY FLOAT64 DATA SHOULD BE PASSED TO B64_ENCODE....!!!!!!!
def b64_encode(float_array):
  return base64.b64encode(float_array)

def get_flat_list_histogram_for_image_obj(im, nmb_histogram_bins):
  nmb_channels = None
  if len(im.shape) == 3 and im.shape[2] == 3:
    nmb_channels = 3
  elif len(im.shape) == 2:
    nmb_channels = 1
  if nmb_channels is None:
    print 'ERR not 1 or 3 chans',im.shape
    return None

  # make sure that we're dealing with 3 channel images only
  im = im.reshape(im.shape[0] * im.shape[1], nmb_channels)

  c_histograms = [np.histogram(im[:,_], bins=nmb_histogram_bins,
                                  density=HIST_USE_DENSITY, range=(0,255))[0] \
                                                  for _ in range(nmb_channels)]

  if nmb_channels == 1:
    # propagate single channel histogram values into rgb channels
    c_histograms = c_histograms * 3
  return np.array(list(chain.from_iterable(c_histograms)))

def get_sub_rect(img, x0, y0, width, height):
  return np.copy(img[y0:y0 + height, x0:x0 + width])

def get_multi_hist(im):
  h, w = im.shape[:2]
  x_delta = w/3
  y_delta = h/3
  muli_hist_vect = []
  skip_image = False
  for x_idx in range(3):
    if skip_image:
      break
    for y_idx in range(3):
      sub_img = get_sub_rect(im, x0=x_idx*x_delta, y0=y_idx*y_delta, width=x_delta, height=y_delta)
      hist_vector = get_flat_list_histogram_for_image_obj(sub_img, MULTI_HIST_NMB_BINS)
      if hist_vector is None:
        skip_image = True
        break
      muli_hist_vect.append(hist_vector)
  if skip_image:
    return None
  img_multi_hist_vect = np.array(list(chain.from_iterable(muli_hist_vect)))
  return img_multi_hist_vect

def get_hash_distance_results(algo_values_and_options,
          base64_encoded_histogram, max_distance_histogram, nmb_histogram_bins,
          base64_encoded_tf, max_distance_tf,
          src_image_ratio, max_distance_image_ratio,
          base64_encoded_multi_hist, max_distance_multi_hist,
          b64_lines_angle_hist, b64_lines_horiz_dist_hist, b64_lines_vert_dist_hist,
          max_distance_lines_angle, max_distance_lines_horiz_dist, max_distance_lines_vert_dist):
  url = "{}?{}".format(IMAGE_HASHING_WEB_SERVER,
                        urllib.urlencode(algo_values_and_options))
  data = {
    'histogram': base64_encoded_histogram,
    'max_distance_histogram': max_distance_histogram,
    'nmb_histogram_bins': nmb_histogram_bins,
    'tf': base64_encoded_tf,
    'max_distance_tf': max_distance_tf,
    'src_image_ratio': src_image_ratio,
    'max_distance_image_ratio': max_distance_image_ratio,
    'base64_encoded_multi_hist': base64_encoded_multi_hist,
    'max_distance_multi_hist': max_distance_multi_hist
  }

  # if some angle information, send angle and either or both vert/horiz hists
  if b64_lines_angle_hist:
    data.update({
      'max_distance_lines_angle': max_distance_lines_angle,
      'max_distance_lines_horiz_dist': max_distance_lines_horiz_dist,
      'max_distance_lines_vert_dist': max_distance_lines_vert_dist,
      'b64_lines_angle_hist': b64_lines_angle_hist,
    })

    #
    if b64_lines_horiz_dist_hist:
      data['b64_lines_horiz_dist_hist'] = b64_lines_horiz_dist_hist
    if b64_lines_vert_dist_hist:
      data['b64_lines_vert_dist_hist'] = b64_lines_vert_dist_hist

  return requests.post(url, data).json()

@app.route('/imgdiff', methods=['GET', 'POST'])
def imgdiff():
  if request.method == 'GET':
    return redirect('/')

  max_distance_adpw_hash = request.form.get('max_distance_adpw_hash')
  max_distance_adpw_hash = int(max_distance_adpw_hash)

  f_obj = request.files['file']
  img_obj = PIL.Image.open(f_obj)
  np_img = misc.imread(f_obj)

  ######### hash

  algo_func_map = dict([(algo, getattr(imagehash, algo))
                    for algo in ['dhash', 'whash', 'phash']])
  # we reference average_hash everywhere as ahash
  algo_func_map['ahash'] = imagehash.average_hash

  algo_hash_values = {
    'max_distance_adpw_hash': max_distance_adpw_hash
  }
  for algo_name, algo_func in algo_func_map.items():
    algo_hash_values[algo_name] = algo_func(img_obj)

  ########## hist

  nmb_histogram_bins = int(request.form.get('nmb_histogram_bins'))
  img_histogram = get_flat_list_histogram_for_image_obj(np_img,
                                          nmb_histogram_bins=nmb_histogram_bins)
  assert img_histogram is not None, 'Image could not be processed for hist (make sure it is a 3 channel RGB image, preferrably in JPG format)'
  base64_encoded_histogram = b64_encode(img_histogram)

  max_distance_histogram = request.form.get('max_distance_histogram')

  ########### tf

  # re-open & re-read file
  f_obj.seek(0, 0)
  tf_vector = run_inference_on_image_data(f_obj.read())
  # tensorflow returns float32s -- hist uses float64
  # and so it's easier to standardize on that..........!!
  # THIS IS EXTRA SUPER IMPORTANT.... and needs to always be around
  # for tf calculations from images
  tf_vector = tf_vector.astype(np.float64)
  base64_encoded_tf = b64_encode(tf_vector)

  max_distance_tf = request.form.get('max_distance_tf')

  ########### image ratio

  max_distance_image_ratio = request.form.get('max_distance_image_ratio')
  src_image_ratio = img_obj.size[0]/float(img_obj.size[1])

  img_obj.close()

  ########### multi hist

  max_distance_multi_hist = request.form.get('max_distance_multi_hist')
  img_multi_hist = get_multi_hist(np_img)

  assert img_multi_hist is not None, 'Image could not be processed for multi hist'
  base64_encoded_multi_hist = b64_encode(img_multi_hist.astype('float64'))

  ########### lines

  max_distance_lines_angle = request.form.get('max_distance_lines_angle')
  max_distance_lines_vert_dist = request.form.get('max_distance_lines_vert_dist')
  max_distance_lines_horiz_dist = request.form.get('max_distance_lines_horiz_dist')

  b64_lines_angle_hist = None
  b64_lines_horiz_dist_hist = None
  b64_lines_vert_dist_hist = None

  line_vectors = get_hough_line_vectors(np_img)
  if line_vectors is not None:
    b64_lines_angle_hist = b64_encode(line_vectors['angle_hist'].astype('float64'))

    if not np.all(line_vectors['horiz_dist_hist'] == 0):
      b64_lines_horiz_dist_hist = b64_encode(line_vectors['horiz_dist_hist'].astype('float64'))

    if not np.all(line_vectors['vert_dist_hist'] == 0):
      b64_lines_vert_dist_hist = b64_encode(line_vectors['vert_dist_hist'].astype('float64'))

  ########### call hash proximity service for
  ########### hash+hist+tf+image_ratio+multi_hist

  hash_distance_res = get_hash_distance_results(algo_hash_values,
            base64_encoded_histogram, max_distance_histogram, nmb_histogram_bins,
            base64_encoded_tf, max_distance_tf,
            src_image_ratio, max_distance_image_ratio,
            base64_encoded_multi_hist, max_distance_multi_hist,
            b64_lines_angle_hist, b64_lines_horiz_dist_hist, b64_lines_vert_dist_hist,
            max_distance_lines_angle, max_distance_lines_horiz_dist, max_distance_lines_vert_dist)

  # find items that were matched by more than 1 algo
  all_matched_ids = [item for algo, items in hash_distance_res.items() \
                          for item in items.keys()]
  all_matched_ids_count = Counter(all_matched_ids)
  matched_by_more_than_1_algo = filter(lambda _:_[1] > 1, all_matched_ids_count.items())
  # keep the id only
  matched_by_more_than_1_algo = map(operator.itemgetter(0), matched_by_more_than_1_algo)
  # recreate dict as-from-img-hashing-service but with all of the distances from all of the algos
  matched_by_more_than_1_algo_with_hash_distances = {}

  def hash_distances_distances_mult_key(multi_algo_hash_distances):
    # as we're iterating dict over .items(), we get (key, value)
    img_id, algo_distances = multi_algo_hash_distances
    
    all_distances = []
    for algo, distance in algo_distances:
      if algo in ['ahash', 'dhash', 'phash', 'whash']:
        # normalize hash distances
        all_distances.append(distance / 64.0)
      else:
        all_distances.append(distance)

    return reduce(operator.mul, all_distances)

  for img_id in matched_by_more_than_1_algo:
    distances = [(algo, hash_distance_res[algo][img_id]) \
                  for algo in hash_distance_res \
                  if img_id in hash_distance_res[algo]]

    matched_by_more_than_1_algo_with_hash_distances[img_id] = distances

  # sort 'more than 1 algo' matches by mult of all distances
  # (those distances that are related to *hash algos need to be normalized first)
  matched_by_more_than_1_algo_ordered_dict = \
    OrderedDict(sorted(matched_by_more_than_1_algo_with_hash_distances.items(),
                        key=hash_distances_distances_mult_key))

  hash_distance_res['_more_than_1_algo'] = matched_by_more_than_1_algo_ordered_dict

  # for each algo, results are orderless-dict. sort results by proximity,
  # in ascending (hash distance) order
  # except for _more_than_1_algo OrderedDict which is already sorted!

  def image_id_to_src_and_filepath(img_item):
    img_id = img_item[0]
    # annoy index sometimes return incorrect id
    # this was specifically seen with 'lines' index and manhattan distance
    # TODO will need to catch below when get_by_id raises exception
    # and return None; then, will need to filter out these None values
    img_obj = Image.get_by_id(img_id)
    source_name = img_obj.artwork_id.source_name
    new_key = None
    if source_name == 'artsy':
      new_key = ('artsy', '/'.join(img_obj.img_local_path.split('/')[-2:]))
    elif source_name == 'met':
      new_key = ('met', '/'.join(img_obj.img_local_path.split('/')[-3:]))
    # TODO add moma
    # TODO add moma
    # TODO add moma
    return [new_key] + list(img_item[1:])

  ordered_hash_distance_res = OrderedDict()
  for algo in sorted(hash_distance_res):
    # don't re-sort ordereddict on dict value....!!
    if type(hash_distance_res[algo]) == OrderedDict:
      sorted_algo_items = hash_distance_res[algo].items()
    else:
      sorted_algo_items = sorted(hash_distance_res[algo].items(),
                                  key=operator.itemgetter(1))

    sorted_algo_items = map(image_id_to_src_and_filepath, sorted_algo_items)

    ordered_hash_distance_res[algo] = OrderedDict(sorted_algo_items)

  return render_template('img_hashing_results.html',
    ordered_hash_distance_res=ordered_hash_distance_res,
    max_distance_adpw_hash=request.form.get('max_distance_adpw_hash'),
    max_distance_histogram=request.form.get('max_distance_histogram'),
    nmb_histogram_bins=request.form.get('nmb_histogram_bins'),
    max_distance_tf=request.form.get('max_distance_tf'),
    )

@app.route('/')
def index():
  return render_template('img_hashing_index.html',
    max_distance_adpw_hash=request.args.get('max_distance_adpw_hash'),
    max_distance_histogram=request.args.get('max_distance_histogram'),
    nmb_histogram_bins=request.args.get('nmb_histogram_bins'),
    max_distance_tf=request.args.get('max_distance_tf'),
  )

if __name__ == '__main__':
  app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=True)
