from PIL import Image
import sys
import scipy
from scipy import spatial
import imagehash

def generate_ahash(image_path):
  with Image.open(image_path) as im:
    h = imagehash.average_hash(im).hash
  return h.astype(bool).flatten()

def generate_dhash(image_path):
  with Image.open(image_path) as im:
    h = imagehash.dhash(im).hash
  return h.astype(bool).flatten()

def generate_phash(image_path):
  with Image.open(image_path) as im:
    h = imagehash.phash(im).hash
  return h.astype(bool).flatten()

def generate_whash(image_path):
  with Image.open(image_path) as im:
    h = imagehash.whash(im).hash
  return h.astype(bool).flatten()

if __name__ == '__main__':
  v1 = generate_ahash(sys.argv[1])
  v2 = generate_ahash(sys.argv[2])
  print 'distance',scipy.spatial.distance.cdist([v1], [v2])

  for f in [generate_ahash, generate_dhash, generate_phash, generate_whash]:
    print len(f(sys.argv[1]))
