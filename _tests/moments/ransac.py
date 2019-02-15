import numpy as np
from skimage import measure, feature, io, color, draw, transform

img = color.rgb2gray(io.imread("/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/color_histogram_hashing/1000-artsy-images/afwMEtiLiLxgdzsGj4RCug.jpg"))
img = transform.resize(img, (512, 512))

img = feature.canny(img).astype(np.uint8)
img[img > 0] = 255

coords = np.column_stack(np.nonzero(img))

circle_model, inliers = measure.ransac(coords, measure.CircleModel, 20, 3)

line_model, inliers = measure.ransac(coords, measure.LineModelND, 20, 3)
line_model = [__ for _ in line_model.params for __ in _]

print (list(circle_model.params) + list(line_model))