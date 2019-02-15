from lshash import LSHash
import skimage
from skimage.io import imread
import os
from skimage.transform import resize

DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-images/'
IMG_PATH = 'afUTrelGPfkioTllVrxRtQ.jpg'

RESIZED_SIDE_SIZE = 64

img = imread(os.path.join(DIR, IMG_PATH))
img = resize(img, (RESIZED_SIDE_SIZE, RESIZED_SIDE_SIZE))

assert len(img.shape) == 3

lsh = LSHash(128, RESIZED_SIDE_SIZE * RESIZED_SIDE_SIZE * 3)
print map(int, lsh.code(img.flatten())[0])
