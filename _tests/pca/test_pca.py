import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import sklearn
from sklearn.decomposition import RandomizedPCA
import os
from skimage.transform import resize

DIR = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-images/'
IMG_PATH = 'afUTrelGPfkioTllVrxRtQ.jpg'

img = mpimg.imread(os.path.join(DIR, IMG_PATH))
img = resize(img, (64, 64))


orig_shape = img.shape
print orig_shape

img_r = np.reshape(img, (img.shape[0], orig_shape[1]*orig_shape[2]))
print img_r.shape

ipca = RandomizedPCA(8).fit(img_r)
img_c = ipca.transform(img_r)

print('img_c', img_c)
print len(img_c.flatten())
