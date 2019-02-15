import pickle
from tqdm import tqdm
import os
import csv
from string import strip
from models import db, Artwork, Image
import operator
import codecs
import sys

IMG_INFO_PICKLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/met_artwork_to_img_json_data.pickle'
FILES_AND_HASHES_FILE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/MET/metmuseum-images-hashes-the-actual-hashes.txt'

# it matters to have an up-to-date CSV! data does change!
MET_CSV_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/MET/MetObjects-12-02-2018.csv'

ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/artworks.sqlite3'

# forced to define this as we want to support negative ints
# and ''.isdigit() return False on such values...
def is_digit(n):
  try:
    int(n)
    return True
  except ValueError:
    return  False

# converts
# /mnt/volume-nyc1-02/metmuseum/images/images.metmuseum.org/CRDImages/ad/original/DP258771.jpg
# into
# ad/original/DP258771.jpg
def filepath_suffix(_):
  return '/'.join(_.split('/')[-3:])


print 'loading IMG_INFO_PICKLE_PATH'
with open(IMG_INFO_PICKLE_PATH) as f:
  all_artworks_to_images = pickle.load(f)

print 'loading FILES_AND_HASHES_FILE_PATH'
all_downloaded_filepaths_by_suffix = {}
with codecs.open(FILES_AND_HASHES_FILE_PATH, 'r', encoding='latin-1') as f:
  for l in f.readlines():
    # get all line but the 4 hashes (i.e. the filepath)
    # unsplit the filename as it may contain spaces and that's ok...
    file_path = ' '.join(l.strip().split(' ')[:-4])
    # keep 'aa/original/04.3.200_013AA2015.jpg' part of filepaths
    # which we consider to be unique identifier 
    file_path_suffix = filepath_suffix(file_path)
    all_downloaded_filepaths_by_suffix[file_path_suffix] = file_path

print 'loading MET_CSV_PATH'
all_met_data = {}
with open(MET_CSV_PATH) as f:
  csv_met_data = csv.DictReader(f)
  for artwork in csv_met_data:
    object_id = artwork['Object ID']
    all_met_data[int(object_id)] = artwork

db.init(ARTWORKS_SQLITE_PATH)
# db.create_tables([Artwork, Image])

for object_id in tqdm(all_artworks_to_images):
  # object ID found in json api response, possibly with (404?) images
  # which does not exist in the met csv data
  if not object_id in all_met_data:
    continue

  # from met CSV data
  artwork = all_met_data[object_id]

  # from met JSON API responses
  # extract img url only -- pickle also contains bool value indicating
  # if image is public domain/open access
  json_image_full_paths = map(operator.itemgetter(0),
                                              all_artworks_to_images[object_id])
  assert len(json_image_full_paths),\
    ('no images defined in json for artwork', object_id, artwork)

  # use 'aa/original/04.3.200_013AA2015.jpg' part of filepaths as key
  json_images_by_suffix = dict([
    (filepath_suffix(_), _)
    for _ in json_image_full_paths
  ])

  downloaded_images_for_artwork_suffixes = [
    json_suffix
    for json_suffix in json_images_by_suffix
    if json_suffix in all_downloaded_filepaths_by_suffix
  ]
  if not len(downloaded_images_for_artwork_suffixes):
    # no images downloaded for artwork
    continue

  # we're finding that the same image file may be used for multiple artworks
  # ....!!
  # we should not insert a new artwork if all of its images have already been added
  # for another artwork; similarly, it's ok to insert a new artwork but none of its
  # images should have been added beforehand
  all_downloaded_not_inserted_filepaths_by_suffix = {}
  for suffix in downloaded_images_for_artwork_suffixes:
    path = all_downloaded_filepaths_by_suffix[suffix]
    res = Image.select().where(Image.img_local_path == path).execute()
    # image already added, skip it
    if len(res):
      continue
    all_downloaded_not_inserted_filepaths_by_suffix[suffix] = path

  if not len(all_downloaded_not_inserted_filepaths_by_suffix):
    # some downloaded images were found for this artwork
    # but all of them have been already added for 'other' (related..?!) artworks
    continue

  # extract year from all of the places it may live in
  year = [artwork[_]
    for _ in ['Object Date', 'Object End Date', 'Object Begin Date']
    if is_digit(artwork[_])]
  assert len(year), ('no year found', object_id, artwork)
  year = year[0]

  artwork_obj = Artwork(
    source_id = object_id,
    source_name = 'met',
    source_page_url = 'https://metmuseum.org/art/collection/search/{}'.format(object_id),
    title = artwork['Title'],
    artist = artwork['Artist Display Name'],
    year = year,
  )
  artwork_obj.save()

  for image_suffix in all_downloaded_not_inserted_filepaths_by_suffix:
    image_obj = Image(
      artwork_id = artwork_obj.id,
      source_img_url = json_images_by_suffix[image_suffix],
      img_local_path = all_downloaded_not_inserted_filepaths_by_suffix[image_suffix],
    )
    try:
      image_obj.save()
    except:
      print 'ERR inserting into image',\
        ('object_id',object_id,
          'artwork_id',artwork_obj.id,
          'source_img_url',json_images_by_suffix[image_suffix],
          'img_local_path',all_downloaded_not_inserted_filepaths_by_suffix[image_suffix]
          )
