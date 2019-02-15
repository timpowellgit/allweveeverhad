import numpy as np
from skimage import filters
import skimage

# 16 pixels, single channel
src_img = np.array([0.03082192 + 2.19178082e-09] * 16).astype('float64')
src_img = src_img.reshape((4,4))

# will print array of 4x4 NaNs
print(filters.threshold_niblack(src_img))

# will print array of 4x4 NaNs
print(filters.threshold_sauvola(src_img))
