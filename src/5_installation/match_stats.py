import os
from collections import Counter
from models import InstallationImageMatch

def print_stats(file_list):
  out = ['STATS']

  # number of files received from each computer
  img_directories = map(lambda _: os.path.basename(os.path.dirname(_)), file_list)
  img_directories_freq = dict(Counter(img_directories).most_common())
  per_directory_stats = ['{}: {}'.format(k, img_directories_freq[k]) for k in sorted(img_directories_freq.keys())]
  out.append('NMB RECEIVED IMAGES: {}'.format(', '.join(per_directory_stats)))

  # number of scored images
  number_of_scored_images = InstallationImageMatch.select().count()
  out.append('NMB SCORED IMAGES: {}'.format(number_of_scored_images))

  # number of images posted to twitter
  nmb_twitter_posts = InstallationImageMatch.select().where(
                        InstallationImageMatch.twitter_post_id.is_null(False)
                      ).count()
  out.append('NMB TWITTER POSTS: {}'.format(nmb_twitter_posts))

  # number of images posted to web
  nmb_web_posts = InstallationImageMatch.select().where(
                        InstallationImageMatch.posted_to_web_timestamp.is_null(False)
                      ).count()
  out.append('NMB WEB POSTS: {}'.format(nmb_web_posts))

  # number of printed images
  nmb_printed_images = InstallationImageMatch.select().where(
                        InstallationImageMatch.printed_timestamp.is_null(False)
                      ).count()
  out.append('NMB PRINTED IMAGES: {}'.format(nmb_printed_images))

  print ' * '.join(out)
