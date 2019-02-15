import os
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import peewee
from models import db, Artwork, Image

ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3'

ARTIST_TO_ALLPAINTERS_MARKUP_DIR = {
  'Josef Albers': '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/scraping 2 - apr 2018/apr 18 ingestion/allpainters-josef-albers',
  'Ellsworth Kelly': '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/scraping 2 - apr 2018/apr 18 ingestion/allpainters-ellsworth-kelly',
}

db.init(ARTWORKS_SQLITE_PATH)

for artist, markup_dir in ARTIST_TO_ALLPAINTERS_MARKUP_DIR.items():
  file_paths = [_ for _ in os.listdir(markup_dir) if _.endswith('.html')]
  for file_path in tqdm(file_paths):
    with open(os.path.join(markup_dir, file_path)) as f:
      soup = BeautifulSoup(f.read(), 'html.parser')
    for div in soup.find_all('div', class_='tag_block'):
      img_page_url = div.find('a').attrs['href']
      artwork_title = div.find('a').attrs['title'].split(u'\u2014')[0].strip()
      img_url_filepath = div.find('img').attrs['src'].split('/')[-1]

      year = -1
      res = re.search(r'(\d{4})', img_url_filepath)
      if res:
        year = int(res.groups()[0])

      artwork = Artwork(
        source_id = img_url_filepath,
        source_name = 'allpainters',
        source_page_url = img_page_url,
        title = artwork_title,
        artist = artist,
        year = year,
      )
      artwork.save()

      image = Image(
        artwork_id = artwork.id,
        source_img_url = 'http://allpainters.org/wp-content/themes/paint/paintings/full/{}'.format(img_url_filepath),
        img_local_path = '/mnt/volume-nyc1-02/allpainters/img{}'.format(img_url_filepath),
      )
      image.save()
