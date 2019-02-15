import os
import peewee
import pickle
from tqdm import tqdm
from models import db, Artwork, Image
import re

ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3'
IMAGES_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/scraping 2 - apr 2018/jflauda/img'

db.init(ARTWORKS_SQLITE_PATH)

all_images = filter(lambda _: _.endswith('.jpg'), os.listdir(IMAGES_DIR))

for file_name in tqdm(all_images):
  res = re.match(r'^(.+).jpg$', file_name)
  title = res.groups()[0].replace('_', ' ')

  year = -1
  artist = 'Jean-Francois Lauda'
  page_url = 'http://jflauda.com/'

  artwork = Artwork(
    source_id = file_name,
    source_name = 'jflauda',
    source_page_url = page_url,
    title = title,
    artist = artist,
    year = year,
  )
  artwork.save()

  image = Image(
    artwork_id = artwork.id,
    # filenames were changed locally as there were many parens, spaces, etc.
    # abdicating and recording generic url...
    source_img_url = page_url,
    img_local_path = '/mnt/volume-nyc1-02/jflauda/{}'.format(file_name),
  )
  image.save()
