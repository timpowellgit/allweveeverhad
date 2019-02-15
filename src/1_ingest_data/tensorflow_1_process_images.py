from string import strip
import sys
import os
import pickle
from models import db, Image
from tensorflow_classify_image import run_inference_on_images
import random
import operator

PROCESSED_DB_IDS_PICKLE_PATH = os.environ['PROCESSED_DB_IDS_PICKLE_PATH']
ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']

db.init(ARTWORKS_SQLITE_PATH)

def process_filepath_list_write_to_pickle_files(input_filepath_list_path, output_pickle_file):
  with open(input_filepath_list_path) as f:
    filepaths = map(strip, f.readlines())

  with open(PROCESSED_DB_IDS_PICKLE_PATH) as f:
    processed_ids = set(pickle.load(f))

  # single mass sql query! sqlite ftw!
  processed_file_names = Image.select(Image.img_local_path).where(
                            Image.id << processed_ids).tuples()
  processed_file_names = map(operator.itemgetter(0), processed_file_names)

  already_processed = set(filepaths) - set(processed_file_names)
  print 'skipping len db indices:',len(filepaths) - len(already_processed)
  filepaths = list(already_processed)

  # shuffle so that images that take longer to compute (met! vs artsy...)
  # are sent to different processes (so that 1 process doesn't end up dealing with
  # easiest and ends early while other still computes for hours -- which happened for histograms)
  random.shuffle(filepaths)

  with open(output_pickle_file, 'w') as output_f:
    for image_path, image_vector in run_inference_on_images(filepaths):
      database_index = Image.get(Image.img_local_path == image_path).id

      # successively dump tensorflow pickles into output file
      # no need to build up huge arrays!
      pickle.dump((database_index, image_vector), output_f)

if __name__ == '__main__':
  assert len(sys.argv) == 3, 'usage: python {} <LIST_OF_FILEPATHS_FILE> <OUTPUT_PICKLE_FILE_PATTERN>'.format(sys.argv[0])
  assert os.path.isfile(sys.argv[1])
  process_filepath_list_write_to_pickle_files(sys.argv[1], sys.argv[2])
