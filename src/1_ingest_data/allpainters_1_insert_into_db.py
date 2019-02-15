import os
import peewee
import pickle
from tqdm import tqdm
from models import db, Artwork, Image
import re

ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3'
IMAGES_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/scraping apr 2018/allpainters-scraping/img'
ALL_PAINTING_URLS = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/scraping apr 2018/allpainters-scraping/jpgs.txt'

db.init(ARTWORKS_SQLITE_PATH)

all_images = filter(lambda _: _.endswith('.jpg'), os.listdir(IMAGES_DIR))
all_images_filenames = {}
with open(ALL_PAINTING_URLS) as f:
  for line in f:
    is_rothko = 'Mark Rothko' in line
    artist = 'Mark Rothko' if is_rothko else 'Barnett Newman'
    page_url = 'http://allpainters.org/theme/{}'.format('-'.join(artist.lower().split()))
    res = re.search(r'/([^/]+)\.jpg', line)
    filename = '{}.jpg'.format(res.groups()[0])
    all_images_filenames[filename] = {
      'artist': artist,
      'page_url': page_url,
    }

for file_name in tqdm(all_images):
  res = re.match(r'^(.+)-(\d{4}).jpg$', file_name)
  if res:
    title, year = res.groups()
  else:
    title = file_name.replace('.jpg', '')
    year = -1
  title = title.replace('-', ' ')

  image_info = all_images_filenames[file_name]

  artwork = Artwork(
    source_id = file_name,
    source_name = 'allpainters',
    source_page_url = image_info['page_url'],
    title = title,
    artist = image_info['artist'],
    year = year,
  )
  artwork.save()

  image = Image(
    artwork_id = artwork.id,
    source_img_url = 'http://allpainters.org/wp-content/themes/paint/paintings/full/{}'.format(file_name),
    img_local_path = '/mnt/volume-nyc1-02/allpainters/img/{}'.format(file_name),
  )
  image.save()
