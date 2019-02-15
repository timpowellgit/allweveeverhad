import os
import peewee
import pickle
from tqdm import tqdm
from models import db, Artwork, Image
import re
from string import strip

ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3'
IMAGES_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/scraping 2 - apr 2018/guidomolinari/img'

FILENAMES_AND_TITLES_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/scraping 2 - apr 2018/guidomolinari/titles-to-files.txt'
file_names_to_titles = {}
with open(FILENAMES_AND_TITLES_PATH) as f:
  for line in f:
    v, k = line.strip().split(';')
    file_names_to_titles[k] = v

db.init(ARTWORKS_SQLITE_PATH)

all_images = filter(lambda _: _.endswith('.jpg'), os.listdir(IMAGES_DIR))

for file_name in tqdm(all_images):
  res = re.match(r'^(.+).jpg$', file_name)
  title = res.groups()[0].replace('_', ' ')
  if file_name in file_names_to_titles:
    title = file_names_to_titles[file_name]
  year = -1
  res = re.search(r'(\d{4})', title)
  if res:
    year = res.groups()[0]

  artist = 'Guido Molinari'
  page_url = 'http://www.paulkuhngallery.com/artists/guido-molinari'

  artwork = Artwork(
    source_id = file_name,
    source_name = 'guidomolinari',
    source_page_url = page_url,
    title = title,
    artist = artist,
    year = year,
  )
  artwork.save()

  image = Image(
    artwork_id = artwork.id,
    source_img_url = 'http://images.paulkuhngallery.com/www_paulkuhngallery_com/{}'.format(file_name),
    img_local_path = '/mnt/volume-nyc1-02/guidomolinari/{}'.format(file_name),
  )
  image.save()
