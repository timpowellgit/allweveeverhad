import skimage
from skimage.io import imread
from skimage import measure
from skimage.color import rgb2gray

IMG_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/_scans and real artworks from adam/new scans 2/computer2/img027.jpg'

im = skimage.io.imread(IMG_PATH)
im = rgb2gray(im)

mu = measure.moments_central(im)
nu = measure.moments_normalized(mu)
hu = measure.moments_hu(nu)
