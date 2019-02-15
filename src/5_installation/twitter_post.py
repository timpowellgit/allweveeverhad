import tweepy
import os
import inspect
from skimage.io import imread, imsave
from skimage.transform import resize
from models import db, InstallationImageMatch, InstallationConfiguration, Image, Artwork
import re
 
# Consumer keys and access tokens, used for OAuth
consumer_key = 'LXKZWn4MvwNHWo2mtg271lVGd'
consumer_secret = '5USbdkUTPQPxG7vrNclKXRTW2pPtLNmbVAD6KGWde1yrHud1ZU'
access_token = '987783701764411393-X0S32xbqr9nbUgPvXY9iVLOWejV3idH'
access_token_secret = 'tnEfPae5M2HQLT3qTa570vQq4PiX9FPW2FVfIqUJcUNKP'

THUMB_HEIGHT = 512

CURR_FILE_DIR, _ = os.path.split(inspect.stack()[0][1])
TWITTER_THUMBS_DIR_PATH = os.path.join(CURR_FILE_DIR, 'twitter_thumbs')

def find_or_create_resized_thumb(orig_img_file_path):
  src_file_name = os.path.split(orig_img_file_path)[1]
  src_file_name_no_ext = os.path.splitext(src_file_name)[0]

  found_thumbnail = filter(lambda _: _.startswith(src_file_name_no_ext), os.listdir(TWITTER_THUMBS_DIR_PATH))
  if len(found_thumbnail) == 1:
    return os.path.join(TWITTER_THUMBS_DIR_PATH, found_thumbnail[0])

  im = imread(orig_img_file_path)
  h = THUMB_HEIGHT
  w = int(h*im.shape[1]/float(im.shape[0]))
  im = resize(im, (h, w), anti_aliasing=True, mode='constant')
  dest_file_path = os.path.join(TWITTER_THUMBS_DIR_PATH, '{}.jpg'.format(
    src_file_name
  ))
  imsave(dest_file_path, im)
  return dest_file_path

def create_status_from_img_match_obj(img_match_obj, force_base_status=False):
  TWITTER_LEN_MAX = 260

  match_score = img_match_obj.match_score
  image = img_match_obj.image
  artwork = image.artwork_id

  title = artwork.title
  title = title if title is not None and title.strip() is not u'' else 'Untitled'

  artist = artwork.artist
  artist = artist if artist is not None and artist.strip() is not u'' else 'Unknown artist'

  year = artwork.year
  year = year if artwork.year is not None and artwork.year != -1 else "Date unknown"

  base_status = u'{:.2f}%_match: {} "{}", {}'.format(
    match_score,
    artist,
    title,
    year
  )

  if force_base_status:
    return base_status[:TWITTER_LEN_MAX]

  # hard truncate
  if len(base_status) > TWITTER_LEN_MAX:
    return base_status[:TWITTER_LEN_MAX]

  artist_hashtag = None
  if artist is not None and artist.strip() is not '':
    hashtag_sub_pattern = re.compile(ur'\W', re.UNICODE)
    artist_hashtag = hashtag_sub_pattern.sub('', artist)
    artist_hashtag = artist_hashtag.lower()

  tags = ['adambasanta','artfactory','dailyart','contemporaryart','digitalart','allwedeverneedisoneanother',artist_hashtag,'abstractart','abstractpainting','artoftheday','digitalpainting','generativeart','postphotography','artcollector','conceptart','contemporarypainting',]
  # skip artist_hashtag if the value is None
  tags = filter(None, tags)

  def status_plus_tags(nmb_tags):
    return u'{} {}'.format(
      base_status,
      u' '.join([u'#'+_ for _ in tags[:nmb_tags]])
    )
  
  all_statuses = []
  for nmb_tags in range(len(tags)):
    # generate all statuses
    all_statuses.append(status_plus_tags(nmb_tags))

  # only keep post-able ones
  all_statuses = filter(lambda _: len(_) <= TWITTER_LEN_MAX, all_statuses)
  if len(all_statuses):
    # return longest postable one
    return all_statuses[-1]
  # could not add a single tag, bail
  return base_status

def twitter_post(img_path, img_match_obj):
  img_path = find_or_create_resized_thumb(img_path)
  status_str = create_status_from_img_match_obj(img_match_obj)

  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  auth.set_access_token(access_token, access_token_secret) 
  api = tweepy.API(auth)

  # do it
  try:
    res = api.update_with_media(img_path, status_str)
    print 'Successfully posted'
    return res.id
  except Exception as e:
    print 'ERR posting to Twitter',e

  try:
    print 'Attempting to post to Twitter again using simpler status message'
    status_str = create_status_from_img_match_obj(img_match_obj, force_base_status=True)
    res = api.update_with_media(img_path, status_str)
    print 'Successfully posted 2nd time'
    return res.id
  except Exception as e:
    print 'ERR posting to Twitter again, bailing',e

  return None

if __name__ == '__main__':
  ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/artworks-from-linux-pc.sqlite3'
  db.init(ARTWORKS_SQLITE_PATH)
  match = InstallationImageMatch.get(InstallationImageMatch.id == 4434)

  print match.image.artwork_id.artist.strip() == ''
  print match.image.artwork_id.artist.strip() == u''

  print create_status_from_img_match_obj(match)

  # img_path = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/5_installation/_test/twitter/scan-p.jpg'
  # print twitter_post(img_path, match)
