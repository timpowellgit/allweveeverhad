from tqdm import tqdm
import re
import pickle

ALL_HASHES_FILE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/creating-one-meta-db/ARTSY/3.artsy-image-hashes-complete.txt'
SERIALIZED_DEST_FILE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/serialized_data/artsy_hashes.pickle'

# dictionary's key is source_id, as above
all_hashes = {}
hash_names = []

with open(ALL_HASHES_FILE_PATH) as hash_f:
  for line_idx, line in enumerate(tqdm(hash_f, desc='hash file')):
    # get hash names from header line
    if line_idx == 0:
      hash_names = line.strip().split(',')[1:]
      continue

    line = line.strip()
    line_parts = line.split()
    if len(line_parts) != 5:
      print 'ERR!!', (line_idx, line)
      continue

    file_path = line_parts[0]
    source_id = file_path.split('/')[-2]
    file_hash_info = dict(zip(hash_names, line_parts[1:]))

    assert all(re.match(r'^[a-f0-9]+$', v) for v in file_hash_info.values()), \
            (line_idx, line)

    all_hashes[source_id] = {
      'source_id': source_id,
      'file_path': file_path,
      'file_hash_info': file_hash_info
    }

print 'serializing'

with open(SERIALIZED_DEST_FILE_PATH, 'w') as f:
  pickle.dump(all_hashes, f)

print 'done'

# TODO store image info (we should have everything) into db

# TODO print images from sitemap that didn't make it into the hashes
