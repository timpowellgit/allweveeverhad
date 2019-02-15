import random
import os
from PIL import Image
import imagehash
from tqdm import tqdm
import numpy as np
from annoy import AnnoyIndex

IMG_DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-images'
ANNOY_INDEX_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/_annoy_tests/imghashes.ann'

NMB_ANNOY_TREES = 1
NMB_HASH_VECTORS = 64

img_filepaths = filter(lambda _: _.endswith('.jpg'), os.listdir(IMG_DIR))
img_needle_filepath = random.choice(img_filepaths)

# TODO start with one hash algo, then check for all 4

dist_to_needle = {}

needle_ahash = imagehash.average_hash(Image.open(os.path.join(IMG_DIR, img_needle_filepath)))
needle_ahash_hash = needle_ahash.hash.astype(int)
needle_ahash_hash = needle_ahash_hash.reshape(1, NMB_HASH_VECTORS)[0]

annoy_index = AnnoyIndex(NMB_HASH_VECTORS, metric='hamming')

for img_idx, img_filepath in enumerate(tqdm(img_filepaths)):
  ahash = imagehash.average_hash(Image.open(os.path.join(IMG_DIR, img_filepath)))
  dist_to_needle[img_filepath] = needle_ahash - ahash
  
  hash_int_array = ahash.hash.astype(int).reshape(1, NMB_HASH_VECTORS)[0]
  annoy_index.add_item(img_idx, hash_int_array)

annoy_index.build(NMB_ANNOY_TREES)
annoy_index.save(ANNOY_INDEX_PATH)

# retrieve/compare test

annoy_index = AnnoyIndex(NMB_HASH_VECTORS, metric='hamming')
annoy_index.load(ANNOY_INDEX_PATH)

results = annoy_index.get_nns_by_vector(needle_ahash_hash,
  len(img_filepaths),
  include_distances=True)

annoy_results = dict((img_filepaths[k], v) for k,v in zip(*results))

# print('annoy_results', annoy_results)
# print('dist_to_needle', dist_to_needle)

print('annoy_results == dist_to_needle', annoy_results == dist_to_needle)
