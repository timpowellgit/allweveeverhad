# to silence decompression bomb warnings
from PIL import Image
Image.MAX_IMAGE_PIXELS = 1000000000

import time
import os
import sys
from match_stats import print_stats
from models import db, InstallationImageMatch, InstallationConfiguration, Image
from configuration_values import get_web_twitter_threshold, get_print_threshold, \
                            get_force_print_flag, set_force_print_flag, \
                            get_force_print_threshold, \
                            get_stop_printing_flag, set_stop_printing_flag, \
                            get_print_every_once_in_n_matches, \
                            get_web_twitter_every_once_in_n_matches
import magic
from image_resizing import resize_image_for_vectorization
from image_hashing import get_all_algo_vectors_for_image, HIST_NMB_BINS
from image_matching import compute_image_distance
from image_score_weight_adjustment import get_top_img_match_by_weights
from peewee import DoesNotExist, fn
from image_printing import print_file
import datetime
from web_generate import web_generate
from twitter_post import twitter_post
import random
from tqdm import tqdm
import numpy as np

SLEEP_BETWEEN_ITERATIONS_S = 10
RECURSIVE_IMAGES_DIR_PATH = os.environ['INSTALLATION_RECURSIVE_IMAGES_DIR_PATH']
ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']

PRINT_SCHEDULE = {
  'start': {
    'weekday': 2, # WED
    'hour': 11, # 11 AM
  },
  'end': {
    'weekday': 5, # SAT
    'hour': 18, # 6 pm
  }
}

db.init(ARTWORKS_SQLITE_PATH)
db.create_tables([InstallationImageMatch])

initial_file_list = None

def check_now_within_print_schedule():
  now = datetime.datetime.now()

  this_weeks_monday = now - datetime.timedelta(days=now.weekday())
  this_weeks_monday = this_weeks_monday.replace(hour=0,minute=0,second=0,microsecond=0)

  start_day_time = this_weeks_monday + datetime.timedelta(
    days=PRINT_SCHEDULE['start']['weekday'],
    hours=PRINT_SCHEDULE['start']['hour']
  )
  end_day_time = this_weeks_monday + datetime.timedelta(
    days=PRINT_SCHEDULE['end']['weekday'],
    hours=PRINT_SCHEDULE['end']['hour']
  )

  return (now >= start_day_time) and (now <= end_day_time)

def get_recursive_file_set():
  file_list = [os.path.join(dp, f) for dp, dn, fn in os.walk(RECURSIVE_IMAGES_DIR_PATH) for f in fn]
  file_list = filter(lambda _: _.endswith('.jpg'), file_list)
  return set(file_list)

def check_force_print_flag():
  if get_force_print_flag():
    print 'Detected force print flag'
    # clear flag
    set_force_print_flag(False)
    sql_conditions = [InstallationImageMatch.match_score > get_force_print_threshold(),
      InstallationImageMatch.printed_timestamp.is_null(True)]
    sql = InstallationImageMatch.select().where(*sql_conditions).order_by(fn.Random())
    try:
      random_non_printed_result = sql.first()
    except Exception as e:
      print 'ERR while attempting to force print',e
      return
    print ('Found file to print' if random_non_printed_result else 'No file found to print')
    if random_non_printed_result:
      image_file_path = random_non_printed_result.file_path
      print_file(image_file_path)
      random_non_printed_result.printed_timestamp = datetime.datetime.now()
      random_non_printed_result.save()

def do_iteration():
  global initial_file_list

  check_force_print_flag()

  new_file_list = get_recursive_file_set()
  if initial_file_list == new_file_list:
    # no new files, nothing to do!
    return

  # if for some reason number of files decreases, this will still work
  # as it will create an empty set
  new_files_to_process_paths = new_file_list - initial_file_list
  print 'Found {} new file{}'.format(len(new_files_to_process_paths),
    '' if len(new_files_to_process_paths) == 1 else 's')

  for new_file_to_process_path in tqdm(new_files_to_process_paths, desc='processing new files'):
    check_force_print_flag()

    print 'Processing {}'.format(new_file_to_process_path)

    # run magic to get mime type, double check that it is indeed jpg
    file_mime_type = magic.from_file(new_file_to_process_path, mime=True)
    if file_mime_type != 'image/jpeg':
      print 'WARN * SKIPPING new non-jpeg file: {}'.format(new_file_to_process_path)
      continue

    print 'Resizing image'
    resized_image_file_path = resize_image_for_vectorization(new_file_to_process_path)
    print 'Getting all algo vectors'
    algo_vectors = get_all_algo_vectors_for_image(resized_image_file_path)

    # black image detection:
    # first hist bin can be any value
    # second bin can up to 0.02
    # all remaining bins should be very close to 0
    black_image_filter = np.array([[999, 0.02] + [1*10**-5] * (HIST_NMB_BINS - 2)] * 3).flatten()
    black_image_filter_result = black_image_filter - algo_vectors['hist']
    if (black_image_filter_result >= 0).all():
      print 'Received entirely black image. Not processing.'
      continue

    print 'Computing distance to all images'
    img_diff_data = compute_image_distance(algo_vectors, hist_nmb_bins=HIST_NMB_BINS)
    print 'Getting top match'
    top_match = get_top_img_match_by_weights(img_diff_data)
    top_match_index = top_match['index']
    top_match_score = top_match['score']

    top_match_score = min(99.5, top_match_score)

    print 'Top match db index',top_match_index,'score',top_match_score

    try:
      matched_image_obj = Image.get(Image.id == top_match_index)
    except DoesNotExist:
      print 'ERR!! Image db id returned for file {} from annoy could not be found in db: {}'.format(
        new_file_to_process_path,
        top_match_index
        )
      continue

    if matched_image_obj.artwork_id.artist.strip() == u'':
      print 'No artist information, skipping'
      continue

    # it's a match!
    db_match_obj = InstallationImageMatch(
      file_path=new_file_to_process_path,
      image=matched_image_obj,
      match_score=top_match_score
    )
    db_match_obj.save()

    if top_match_score >= get_web_twitter_threshold():
      if random.randrange(get_web_twitter_every_once_in_n_matches()) == 0:
        print 'Updating web site'
        db_match_obj.posted_to_web_timestamp = datetime.datetime.now()
        db_match_obj.save()
        web_generate()

        print 'Posting to Twitter'
        twitter_post_id = twitter_post(db_match_obj.file_path, db_match_obj)
        if twitter_post_id:
          db_match_obj.twitter_post_id = twitter_post_id
          db_match_obj.save()

    if get_stop_printing_flag():
      print 'Stop printing flag detected, not attempting to print'
      continue

    if not check_now_within_print_schedule():
      print 'Not within print schedule, not attempting to print'
      continue

    if not (top_match_score >= get_print_threshold()):
      print 'Score lower than print threshold, not attempting to print'
      continue

    if not (random.randrange(get_print_every_once_in_n_matches()) == 0):
      print 'Dice roll did not land on 0, not attempting to print'
      continue

    # WE DID IT
    print 'All conditions pass, printing image'
    print_file(new_file_to_process_path)
    db_match_obj.printed_timestamp = datetime.datetime.now()
    db_match_obj.save()

  initial_file_list = new_file_list

if __name__ == '__main__':
  initial_file_list = get_recursive_file_set()
  while True:
    do_iteration()
    # initial_file_list will be updated to have latest list of files
    print_stats(initial_file_list)
    print 'Waiting {} seconds'.format(SLEEP_BETWEEN_ITERATIONS_S)
    time.sleep(SLEEP_BETWEEN_ITERATIONS_S)
    sys.stdout.flush()
