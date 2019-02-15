from string import strip

ALL_IMAGE_URLS_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/MET/all-image-urls.txt'

FILES_AND_HASHES_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/MET/metmuseum-images-hashes-the-actual-hashes.txt'

with open(ALL_IMAGE_URLS_PATH) as f:
  all_image_urls = map(strip, f.readlines()[1:])
  all_image_urls = map(lambda _: _.split('/')[-1], all_image_urls)

print all_image_urls[:5]

with open(FILES_AND_HASHES_PATH) as f:
  all_downloaded_files = map(strip, f.readlines()[1:])
  all_downloaded_files = map(lambda s: s.split()[0].split('/')[-1],\
                          all_downloaded_files)

print all_downloaded_files[:5]

# LOOKS LIKE THEY'RE ALL (except 1 I found in sample of 20) 404....!!
print list(set(all_image_urls) - set(all_downloaded_files))[10:20]