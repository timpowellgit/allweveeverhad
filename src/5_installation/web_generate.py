from jinja2 import Environment, FileSystemLoader, Template
from string import strip
import os
import operator
import random
from skimage.io import imread, imsave
from skimage.transform import resize
import inspect
from subprocess import call
from models import db, InstallationImageMatch, InstallationConfiguration, Image, Artwork
from tqdm import tqdm
from itertools import groupby
from collections import defaultdict
from datetime import datetime

import getpass
import platform
DEBUG_ENV = getpass.getuser() == 'greg' and platform.system() == 'Darwin'

# to silence low contrast warnings
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

SQL_MIN_DATE = datetime(2018, 5, 1)

THUMB_HEIGHT = 180
FULL_IMG_LONGEST_SIDE = 640
MAX_BEST_MATCHES = 50 if not DEBUG_ENV else 1

SURGE_BIN = os.environ['SURGE_BIN']

CURR_FILE_DIR, _ = os.path.split(inspect.stack()[0][1])
TEMPLATES_DIR = os.path.join(CURR_FILE_DIR, 'web_templates')
DIST_DIR = os.path.join(CURR_FILE_DIR, 'web_dist')
DIST_THUMB_IMG_DIR_PATH = os.path.join(DIST_DIR, 'img')
DIST_FULL_IMG_DIR_PATH = os.path.join(DIST_DIR, 'full')

j2_env = Environment(loader=FileSystemLoader(os.path.join(TEMPLATES_DIR)), trim_blocks=True)

def render_template_to_file_with_vars(template_path, output_filename, template_vars):
  template = j2_env.get_template(template_path)
  rendered_template = template.render(**template_vars)
  with open(os.path.join(DIST_DIR, output_filename), 'w') as f:
    f.write(rendered_template.encode('utf-8'))

def generate_about_page(template_vars):
  render_template_to_file_with_vars('about.html', 'about.html', template_vars)

def generate_image_page(images, output_filename, template_vars):
  template_vars['images'] = images
  render_template_to_file_with_vars('image_list.html', output_filename, template_vars)

def find_or_create_resized_thumb(orig_img_file_path, dest_dir_path, thumb_size,
                            max_height_mode=False, max_longest_side_mode=False):
  src_file_name = os.path.split(orig_img_file_path)[1]
  src_file_name_no_ext = os.path.splitext(src_file_name)[0]
  found_thumbnail = filter(lambda _: _.startswith(src_file_name_no_ext), os.listdir(dest_dir_path))
  if len(found_thumbnail) == 1:
    return os.path.join(dest_dir_path, found_thumbnail[0])

  im = imread(orig_img_file_path)
  orientation = 'p' if im.shape[0] > im.shape[1] else 'l'

  if max_height_mode:
    h = thumb_size
    w = int(h*im.shape[1]/float(im.shape[0]))
  if max_longest_side_mode:
    if im.shape[0] > im.shape[1]:
      h = thumb_size
      w = int(h*im.shape[1]/float(im.shape[0]))
    else:
      w = thumb_size
      h = int(w*im.shape[0]/float(im.shape[1]))

  im = resize(im, (h, w), anti_aliasing=True, mode='constant')
  dest_file_path = os.path.join(dest_dir_path, '{}_{}.jpg'.format(
    os.path.splitext(src_file_name)[0],
    orientation
  ))
  imsave(dest_file_path, im)
  return dest_file_path

def match_object_to_template_obj(match_obj):
  image = match_obj.image
  artwork = image.artwork_id

  orig_file_path = match_obj.file_path

  if DEBUG_ENV:
    orig_file_path = orig_file_path.replace('/mnt/quickmaths', '/Volumes')

  thumb_img_path = find_or_create_resized_thumb(
    orig_img_file_path=orig_file_path,
    dest_dir_path=DIST_THUMB_IMG_DIR_PATH,
    thumb_size=THUMB_HEIGHT,
    max_height_mode=True)
  thumb_img_file_name = os.path.split(thumb_img_path)[1]
  thumb_img_orientation = os.path.splitext(thumb_img_file_name)[0].split('_')[1]

  full_img_path = find_or_create_resized_thumb(
    orig_img_file_path=orig_file_path,
    dest_dir_path=DIST_FULL_IMG_DIR_PATH,
    thumb_size=FULL_IMG_LONGEST_SIDE,
    max_longest_side_mode=True)
  full_img_file_name = os.path.split(full_img_path)[1]

  title = artwork.title
  title = title if title is not None and title.strip() is not u'' else 'Untitled'

  artist = artwork.artist
  artist = artist if artist is not None and artist.strip() is not u'' else 'Unknown artist'

  year = artwork.year
  year = year if artwork.year is not None and artwork.year != -1 else "Date unknown"

  return {
    'match_score': '%.2f' % match_obj.match_score,
    'artist': artist,
    'title': title,
    'year': year,
    'thumb_img_file_name': thumb_img_file_name,
    'thumb_img_orientation': thumb_img_orientation,
    'full_img_file_name': full_img_file_name
  }

def ord(n):
    return str(n)+("th" if 4<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10, "th"))
def dtStylish(dt,f):
    return dt.strftime(f).replace("{th}", ord(dt.day))

def generate_all_image_pages(template_vars):
  print 'Generating all image pages'

  # web matches after May 1st
  base_query = InstallationImageMatch.select().where(
    InstallationImageMatch.posted_to_web_timestamp.is_null(False),
    InstallationImageMatch.created_timestamp >= SQL_MIN_DATE
  )

  if DEBUG_ENV:
    base_query = base_query.limit(5)

  # this query is shared by image-by-date pages, and the index page
  most_recent = base_query.order_by(InstallationImageMatch.posted_to_web_timestamp.desc())
  most_recent_matches = most_recent.execute()

  # start with dates, as this is necessary to generate side bar menu
  # then pass date links as template_vars to all other funcs
  # N x by date - yyyymmdd.html
  # group best_matches by date
  print 'Grouping generated images by date'
  grouped_matches = defaultdict(list)
  for match in most_recent_matches:
    grouped_matches[match.created_timestamp.strftime('%Y%m%d')].append(match)
  for match_date, match_date_objects in grouped_matches.items():
    grouped_matches[match_date] = sorted(match_date_objects, key=lambda _: _.created_timestamp, reverse=True)

  # pass generated dates links to all further generate_image_page calls
  print 'Generating sidebar date links'
  date_links = []
  for date_str, matched_objects in sorted(grouped_matches.items(), key=operator.itemgetter(0), reverse=True):
    date_links.append({
      'date': date_str,
      'date_english': dtStylish(matched_objects[0].created_timestamp, '%B {th}'),
      'link_color': random.choice(['dark-red','red','light-red','orange','gold','yellow','light-yellow','purple','light-purple','dark-pink','hot-pink','pink','light-pink','dark-green','green','light-green','navy','dark-blue','blue','light-blue','lightest-blue','washed-blue','washed-green','washed-yellow','washed-red',])
    })
  template_vars['dates_links'] = date_links

  print 'Generating image-by-date pages'
  # images by date - <yymmdd>.html
  for group_date, grouped_date_images in grouped_matches.items():
    grouped_date_template_objects = map(match_object_to_template_obj, tqdm(grouped_date_images, desc='Resizing'))
    generate_image_page(grouped_date_template_objects, '{}.html'.format(group_date), dict(
      template_vars.items() + {'showdates': True}.items()
    ))

  # homepage and most recent - index.html
  print 'Generating most recent (index) page'
  most_recent_template_objects = map(match_object_to_template_obj, tqdm(most_recent_matches))
  generate_image_page(most_recent_template_objects, 'index.html', template_vars)

  print 'Generating most recent page with auto-reloader'
  most_recent_template_objects = map(match_object_to_template_obj, tqdm(most_recent_matches))
  generate_image_page(most_recent_template_objects, 'mostrecentautoreload.html', dict(
    template_vars.items() + {'keep_reloading': True}.items()
  ))

  # best matches - bestmatches.html
  print 'Generating best matches page'
  best_matches = base_query.order_by(InstallationImageMatch.match_score.desc())
  best_matches_results = best_matches.limit(MAX_BEST_MATCHES)

  best_matches_template_objects = map(match_object_to_template_obj, tqdm(best_matches_results))
  generate_image_page(best_matches_template_objects, 'bestmatches.html', template_vars)

  return template_vars

def surge_deploy():
  print 'Deploying'
  call([SURGE_BIN, DIST_DIR])

def web_generate():
  print 'Generating web site'
  # need to generate image pages first to get date sidebar links
  template_vars = generate_all_image_pages({})
  generate_about_page(template_vars)
  surge_deploy()

if __name__ == '__main__':
  ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']
  db.init(ARTWORKS_SQLITE_PATH)

  template_vars = generate_all_image_pages({})
  generate_about_page(template_vars)
