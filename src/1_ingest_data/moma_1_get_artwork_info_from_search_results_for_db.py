import os
from tqdm import tqdm
import base64
import json
import re
from models import db, Artwork, Image


DOWNLOADED_FILES_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/MOMA/take-2-at-finding-all-image-paths/all-downloaded-moma-images.txt'
SEARCH_RESULTS_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/MOMA/take-2-at-finding-all-image-paths/search-results'
ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artworks.sqlite3'


db.init(ARTWORKS_SQLITE_PATH)


def decode_base64(data):
  missing_padding = len(data) % 4
  if missing_padding != 0:
      data += b'='* (4 - missing_padding)
  return base64.decodestring(data)

# use image id, instead of collection id as key
# as we can get former from image filename
all_downloaded_by_img_id = {}

with open(DOWNLOADED_FILES_PATH) as f:
  for filename in tqdm(f):
    filename = filename.strip()
    filename = filename.split('/media/')[1]

    artwork_id = filename.split('.jpg')[0]
    artwork_id = decode_base64(artwork_id)
    artwork_id = int(json.loads(artwork_id)[0][1])

    all_downloaded_by_img_id[artwork_id] = filename

re_author = re.compile(r'<h2 class="tile__caption tile__caption--3lines center">([^<]+)<div')
re_author_alt = re.compile(r'<h2 class="tile__caption tile__caption--3lines center"><a[^>]+>([^<]+)</a>')
re_title = re.compile(r'<div class="(object-title|)">(.+?)</div>')
re_year = re.compile(r'</div>([^<]+)</h2><(/a>|div)')
re_collection_id = re.compile(r'href="/collection/works/([^\?]+)\?')
re_img_id = re.compile(r'/media/([^.]+)\.jpg\?sha=([0-9a-f]+)')

# same as all_downloaded: use image id, instead of collection id as key
# as we can get former from image filename
all_artwork_by_img_id = {}

def clean_artwork_markup(s):
  s = s.replace('\n', '')
  s = re.sub('> +<', '><', s)
  return re.sub(' +', ' ', s)

def strip_tags(s):
  return re.sub(r'<[^>]+>', '', s)

def clean_year(s):
  res = re.search(r'([0-9]){4}', s)
  if res:
    return int(res.groups()[0])
  else:
    return -1

for filename in tqdm(filter(lambda _: _.startswith('works?'), os.listdir(SEARCH_RESULTS_DIR)),
                      desc='search result'):
  path = os.path.join(SEARCH_RESULTS_DIR, filename)
  with open(path) as f:
    artworks = f.read().split('<div class="tile tile--height"')[1:]
    if len(artworks) == 0:
      continue
    artworks[-1] = artworks[1:][-1].split('<div class="tile__gradient tile__gradient--3lines">')[0]

    artworks = map(clean_artwork_markup, artworks)

    for artwork in tqdm(artworks, desc='artworks'):
      if 'No image available' in artwork:
        continue

      try:
        img_id = re_img_id.search(artwork).groups()[0]
      except:
        print 'ERR img_id not found!!!',path,artwork
      img_id = int(json.loads(decode_base64(img_id))[0][1])

      if img_id not in all_downloaded_by_img_id:
        # image not found -- not that bad, as it happens only 8 / 60k times
        continue

      collection_id = re_collection_id.search(artwork).groups()[0]

      # if found, skip
      # if not skip, insert...
      try:
        Artwork.get((Artwork.source_id == collection_id) & 
          (Artwork.source_name == 'moma'))
        continue
      except Artwork.DoesNotExist:
        pass

      title = re_title.search(artwork)
      if title:
        title = strip_tags(title.groups()[1])
      else:
        title = 'Untitled'

      author = re_author.search(artwork)
      if not author:
        author = re_author_alt.search(artwork)
      author = author.groups()[0]

      year = re_year.search(artwork)
      if year:
        year = clean_year(year.groups()[0])
      else:
        year = -1

      # same image may be used by multiple artworks...
      # those artworks are duplicates really then...
      # skip artwork/image in these cases!

      img_local_path = '/mnt/volume-nyc1-02/moma/images/www.moma.org/media/{}'.format(all_downloaded_by_img_id[img_id])

      try:
        Image.get(Image.img_local_path == img_local_path)
        continue
      except Image.DoesNotExist:
        pass

      artwork_data = dict(
        source_id = collection_id,
        source_name = 'moma',
        source_page_url = 'https://www.moma.org/collection/works/{}'.format(collection_id),
        title = title,
        artist = author,
        year = year,
      )
      try:
        db_artwork = Artwork(**artwork_data)
        db_artwork.save()
      except Exception as e:
        print 'ERR saving artwork', artwork_data
        raise e

      image_data = dict(
        artwork_id = db_artwork.id,
        source_img_url = 'https://www.moma.org/media/{}'.format(all_downloaded_by_img_id[img_id]),
        img_local_path = img_local_path,
      )
      try:
        db_image = Image(**image_data)
        db_image.save()
      except Exception as e:
        print 'ERR saving image', image_data
        raise e
