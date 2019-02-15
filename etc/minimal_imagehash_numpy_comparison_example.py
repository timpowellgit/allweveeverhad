import os
import pandas as pd
from PIL import Image
import imagehash
import numpy

DIR = '/Users/greg/Desktop'

hashes = []
for filename in ['a.jpg', 'b.jpg', 'c.jpg']:
  with open(os.path.join(DIR, filename)) as f:
    hashes.append(imagehash.whash(Image.open(f)).hash.flatten())

hashes = pd.Series(hashes)

with open(os.path.join(DIR, 'needle.jpg')) as f:
  needle = imagehash.whash(Image.open(f)).hash.flatten()

print numpy.count_nonzero(needle != hashes, axis=1)

"""
SHOULD BE:

('hashes.shape', (3, 64))
('hashes.dtype', dtype('bool'))

('needle.shape', (64,))
('needle.dtype', dtype('bool'))
"""