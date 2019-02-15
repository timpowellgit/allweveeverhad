from models import db, Artwork, Image
from tqdm import tqdm
import pickle
import os
from get_image_size import get_image_metadata

DEBUG = False

ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']
OUTPUT_LINE_PICKLE_PATH = os.environ['OUTPUT_LINE_PICKLE_PATH']

db.init(ARTWORKS_SQLITE_PATH)

all_db_image_ids_paths = Image.select(Image.id, Image.img_local_path).tuples()

if DEBUG:
  dir = '/Volumes/Phatty/ART-freeriots-to-make-more-room-on-tw/___scans and real artworks from adam/4 even newer scans/computer2/'
  all_db_image_ids_paths = [(_, os.path.join(dir, 'comp2img{:03d}.jpg'.format(_))) for _ in range(1, 20)]

with open(OUTPUT_LINE_PICKLE_PATH, 'w') as f:
  for image_id, image_path in tqdm(all_db_image_ids_paths):
    if not image_path:
      continue
    try:
      img_data = get_image_metadata(image_path)
    except:
      continue
    ratio = img_data.width/float(img_data.height)
    pickle.dump((image_id, ratio), f)
