import os
import tempfile
from flask import Flask, request, render_template
from hashing_algos.adpwhash import generate_ahash, generate_dhash, generate_phash, generate_whash
from hashing_algos.hist import generate_hist, generate_multi_hist
from hashing_algos.tf import generate_tf
from hashing_algos.image_ratio import generate_image_ratio
from hashing_algos.lines import get_hough_line_vectors
import base64
from tqdm import tqdm
import requests
import urllib
import numpy as np
import shutil
import json
from skimage.io import imread, imsave
from skimage.transform import resize
import sys
import time

app = Flask(__name__)

IMAGE_HASHING_WEB_SERVER = 'http://localhost:9999/'

REALTIME_DIFF_PICKLE_PATH = os.environ['REALTIME_DIFF_PICKLE_PATH']
REALTIME_DIFF_PICKLE_DEST_DIR = os.environ['REALTIME_DIFF_PICKLE_DEST_DIR']

# TODO 10 upload form GET page
# will need to pick

# TODO hash/hist/tf incoming 10 images
# make calls to hash_proximity_server
# rename/move files pickle files to keep all 100 at once
# use file hash as part of renamed pickle file name? not 'just' idx?

def _binary_array_to_hex(arr):
  """
  internal function to make a hex string out of a binary array.
  """
  bit_string = ''.join(str(b) for b in 1 * arr.flatten())
  width = int(np.ceil(len(bit_string)/4))
  return '{:0>{width}x}'.format(int(bit_string, 2), width=width)

def get_hash_distance_results(algo_values_and_options,
          base64_encoded_histogram, nmb_histogram_bins,
          base64_encoded_tf,
          src_image_ratio,
          base64_encoded_multi_hist,
          b64_lines_angle_hist, b64_lines_horiz_dist_hist, b64_lines_vert_dist_hist):
  url = "{}?{}".format(IMAGE_HASHING_WEB_SERVER,
                        urllib.urlencode(algo_values_and_options))
  data = {
    'histogram': base64_encoded_histogram,
    'nmb_histogram_bins': nmb_histogram_bins,
    'tf': base64_encoded_tf,
    'src_image_ratio': src_image_ratio,
    'base64_encoded_multi_hist': base64_encoded_multi_hist,
  }

  # if some angle information, send angle and either or both vert/horiz hists
  if b64_lines_angle_hist:
    data.update({
      'b64_lines_angle_hist': b64_lines_angle_hist,
    })

    #
    if b64_lines_horiz_dist_hist:
      data['b64_lines_horiz_dist_hist'] = b64_lines_horiz_dist_hist
    if b64_lines_vert_dist_hist:
      data['b64_lines_vert_dist_hist'] = b64_lines_vert_dist_hist
  return requests.post(url, data).json()

@app.route('/results-only')
def results_only():
  return render_template('results.html',
    files_base64_encoded=json.dumps([])
  )

def process_image_file(file_path, nmb_histogram_bins, file_key):
  # read, and then save back resized src image

  tmp_resized_img_dir = tempfile.mkdtemp()
  _, dest_resized_file_name = os.path.split(file_path)
  dest_resized_file_path = os.path.join(tmp_resized_img_dir, dest_resized_file_name)

  im = imread(file_path)
  width = im.shape[1]
  ratio = width / 512.0
  im = resize(im, (int(im.shape[0] / ratio), 512), anti_aliasing=True)
  imsave(dest_resized_file_path, im)

  url_hash_values = {
    'ahash': generate_ahash(dest_resized_file_path),
    'dhash': generate_dhash(dest_resized_file_path),
    'phash': generate_phash(dest_resized_file_path),
    'whash': generate_whash(dest_resized_file_path),
  }
  url_hash_values = dict([(k, _binary_array_to_hex(v)) for k,v in url_hash_values.items()])

  image_ratio = generate_image_ratio(dest_resized_file_path)
  multi_hist_vector = generate_multi_hist(dest_resized_file_path)
  line_info = get_hough_line_vectors(dest_resized_file_path)

  b64_lines_angle_hist=None
  b64_lines_horiz_dist_hist=None
  b64_lines_vert_dist_hist=None
  if line_info:
    b64_lines_angle_hist=base64.b64encode(line_info['angle_hist'].astype(np.float64))
    b64_lines_horiz_dist_hist=base64.b64encode(line_info['horiz_dist_hist'].astype(np.float64))
    b64_lines_vert_dist_hist=base64.b64encode(line_info['vert_dist_hist'].astype(np.float64))
  get_hash_distance_results(algo_values_and_options=url_hash_values,
    base64_encoded_histogram=base64.b64encode(generate_hist(dest_resized_file_path, nmb_histogram_bins)),
    nmb_histogram_bins=nmb_histogram_bins,
    base64_encoded_tf=base64.b64encode(generate_tf(dest_resized_file_path).astype(np.float64)),
    src_image_ratio=generate_image_ratio(dest_resized_file_path)[0],
    base64_encoded_multi_hist=base64.b64encode(generate_multi_hist(dest_resized_file_path).astype(np.float64)),
    b64_lines_angle_hist=b64_lines_angle_hist,
    b64_lines_horiz_dist_hist=b64_lines_horiz_dist_hist,
    b64_lines_vert_dist_hist=b64_lines_vert_dist_hist,
  )

  dest_pickle_path = os.path.join(REALTIME_DIFF_PICKLE_DEST_DIR, '{}.pickle'.format(file_key))
  shutil.move(REALTIME_DIFF_PICKLE_PATH, dest_pickle_path)
  return dest_pickle_path

@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
    for the_file in os.listdir(REALTIME_DIFF_PICKLE_DEST_DIR):
      file_path = os.path.join(REALTIME_DIFF_PICKLE_DEST_DIR, the_file)
      try:
          if os.path.isfile(file_path):
              os.unlink(file_path)
      except Exception as e:
          print(e)
    return render_template('index.html')

  nmb_histogram_bins = int(request.form.get('nmb_histogram_bins'))

  files_base64_encoded = []
  file_obj_temp_dest_dir = tempfile.mkdtemp()
  file_uploads = request.files.getlist("files[]")
  for file_upload_idx, file_upload_f in enumerate(tqdm(file_uploads)):
    file_key = 'file{}'.format(file_upload_idx)
    _, extension = os.path.splitext(file_upload_f.filename)
    # write received image file to temporary file
    temp_dest_filename = os.path.join(file_obj_temp_dest_dir, '{}{}'.format(file_key, extension))
    with open(temp_dest_filename, 'w') as dest_f:
      file_obj_data = file_upload_f.read()
      dest_f.write(file_obj_data)

    files_base64_encoded.append(base64.b64encode(file_obj_data))
    print "Sending %s to hash proximity server" %(file_upload_f.filename)
    process_image_file(temp_dest_filename, nmb_histogram_bins, file_key)

  return render_template('results.html',
    files_base64_encoded=json.dumps(files_base64_encoded)
  )

if __name__ == '__main__':
  app.run(host='localhost', port=9998, debug=True, use_reloader=True, threaded= True)
