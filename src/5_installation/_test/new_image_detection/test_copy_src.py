import shutil
import uuid
import time
import os

TIME_BETWEEN_NEW_IMAGE_CREATION_S = 10

SRC_IMG = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/5_installation/_test/new_image_detection/images_dir/src.jpg'

DEST_DIR_BASE_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/5_installation/_test/new_image_detection/images_dir'
DEST_DIRS = ['comp1', 'comp2']

while True:
  for dest_dir in DEST_DIRS:
    dest_dir_path = os.path.join(DEST_DIR_BASE_DIR, dest_dir)
    dest_file_name = '{}.jpg'.format(str(uuid.uuid4()))
    dest_file_path = os.path.join(dest_dir_path, dest_file_name)
    shutil.copy(SRC_IMG, dest_file_path)
  time.sleep(TIME_BETWEEN_NEW_IMAGE_CREATION_S)
