import peewee
import pickle
from tqdm import tqdm
from models import db, Artwork, Image

SITEMAPS_PICKLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_sitemaps.pickle'
HASHES_PICKLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_hashes.pickle'
ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/artworks.sqlite3'

print 'reading sitemaps'
with open(SITEMAPS_PICKLE_PATH) as f:
  all_sitemaps = pickle.load(f)

print 'reading hashes'
with open(HASHES_PICKLE_PATH) as f:
  all_hashes = pickle.load(f)

db.init(ARTWORKS_SQLITE_PATH)
db.create_tables([Artwork, Image])

for curr_img_hash in tqdm(all_hashes.values()):
  source_id = curr_img_hash['source_id']

  curr_img_sitemap = all_sitemaps.get(source_id)

  if curr_img_sitemap is None:
    print 'ERR not found in sitemaps', curr_img_hash
    continue

  artwork = Artwork(
    source_id = source_id,
    source_name = 'artsy',
    source_page_url = curr_img_sitemap['source_page_url'],
    title = curr_img_sitemap['title'],
    artist = curr_img_sitemap['artist'],
    year = curr_img_sitemap.get('year'),
  )
  artwork.save()

  image = Image(
    artwork_id = artwork.id,
    source_img_url = curr_img_sitemap['source_img_url'],
    img_local_path = curr_img_hash['file_path'],
  )
  image.save()
