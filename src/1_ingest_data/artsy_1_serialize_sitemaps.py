from models import Artwork, db
from peewee import SqliteDatabase
import os
from xml.etree import ElementTree
import re
from tqdm import tqdm
import pickle

SITEMAP_XML_FILES_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/ARTSY/artsy-data/sitemap-images'
SERIALIZED_DEST_FILE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/serialized_data/artsy_sitemaps.pickle'

RE_CAPTION_NO_YEAR = r'^(?P<title>.+) is a work of art created by (?P<artist>.+).$'
RE_CAPTION_WITH_INT_YEAR = r'^(?P<title>.+) is a work of art created by (?P<artist>.+) in (?P<year>\d+).$'
RE_CAPTION_WITH_CA_INT_YEAR = r'^(?P<title>.+) is a work of art created by (?P<artist>.+) in ca\. (?P<year>\d+).$'

db.init('../artworks.sqlite3')
# will not unnecessarily re-create tables
db.create_tables([Artwork])

ns = {'url': 'http://www.sitemaps.org/schemas/sitemap/0.9',
      'image': 'http://www.google.com/schemas/sitemap-image/1.1'}

# dictionary's key is artsy's source ID
all_data_artsy_from_sitemaps = {}

print 'loading data from artsy sitemap files'

# load all sitemap xml files in memory to have reference of all images
xml_files = os.listdir(SITEMAP_XML_FILES_DIR)
xml_files = sorted(filter(lambda _: _.endswith('.xml'), xml_files))
for file_path in tqdm(xml_files, desc='files'):
  path = os.path.join(SITEMAP_XML_FILES_DIR, file_path)

  tree = ElementTree.parse(path)
  root = tree.getroot()

  # one <url> == one artwork
  for url_tag in tqdm(root, desc='tags'):
    loc_tag = url_tag.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
    assert len(loc_tag.text) > 0

    image_tag = url_tag.find('{http://www.google.com/schemas/sitemap-image/1.1}image')
    image_loc_tag = image_tag.find('{http://www.google.com/schemas/sitemap-image/1.1}loc')
    assert len(image_loc_tag.text) > 0
    image_caption_tag = image_tag.find('{http://www.google.com/schemas/sitemap-image/1.1}caption', ns)
    assert len(image_caption_tag.text) > 0

    # cleanup gremlins
    image_caption_tag_text = image_caption_tag.text.replace('\n', '')

    # match patterns (from 'most complicated' to simplest)
    # until we find one that matches. if none match, raise.
    for pattern in [RE_CAPTION_WITH_CA_INT_YEAR,
                    RE_CAPTION_WITH_INT_YEAR,
                    RE_CAPTION_NO_YEAR,
                    ]:
      res = re.match(pattern, image_caption_tag_text)
      if res:
        break

    assert res, (path, url_tag, image_caption_tag.text)
    art_info = res.groupdict()

    assert (len(art_info['title']) > 0 and len(art_info['artist']) > 0 
            and ('year' not in art_info or art_info['year'].isdigit())), \
              (path, url_tag, image_caption_tag.text, art_info)

    source_id = image_loc_tag.text.split('/')[-2]

    art_info.update({
      'source_id': source_id,
      'source_page_url': loc_tag.text,
      'source_img_url': image_loc_tag.text,
    })
    all_data_artsy_from_sitemaps[source_id] = art_info

print 'loaded data from artsy, serializing'

with open(SERIALIZED_DEST_FILE_PATH, 'w') as f:
  pickle.dump(all_data_artsy_from_sitemaps, f)

print 'done'
