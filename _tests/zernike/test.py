import mahotas
from mahotas.features import zernike_moments
import numpy as np
import skimage
from skimage import measure, feature, io, color, draw, transform
from skimage.color import rgb2gray

im = skimage.io.imread('/Users/greg/Downloads/IMG_3412.JPG')
im = rgb2gray(im)
im = mahotas.imresize(im, (256,256))

BLOCK_SIZE = 64

vectors = []
for startx in range(0, 256-32, 32):
  for starty in range(0, 256-32, 32):
    cropped_im = im[starty : starty+BLOCK_SIZE , startx : startx+BLOCK_SIZE]
    vector = zernike_moments(im, radius=BLOCK_SIZE, degree=5)
    vectors.append(vector)

print('len(vectors)', len(vectors), len(vectors[0]))