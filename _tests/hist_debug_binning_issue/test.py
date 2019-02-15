from scipy import misc
import numpy as np
from itertools import chain


TEST_IMAGE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/_tests/hist_debug_binning_issue/1px-255red.png'
TEST_IMAGE_PATH2 = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/_tests/hist_debug_binning_issue/1px-grey.png'


USE_DENSITY = True

def get_flat_list_histogram_for_image_path(path, nmb_bins_list):
  try:
    orig_im = misc.imread(path)
  except:
    print 'ERR opening img!!',path
    return None

  nmb_channels = None
  if len(orig_im.shape) == 3 and orig_im.shape[2] == 3:
    nmb_channels = 3
  elif len(orig_im.shape) == 2:
    nmb_channels = 1
  if nmb_channels is None:
    print 'ERR not 1 or 3 chans',path,orig_im.shape
    return None

  histograms_for_bin_numbers = []
  for nmb_bins in nmb_bins_list:
    # make sure that we're dealing with 3 channel images only
    im = orig_im.reshape(orig_im.shape[0] * orig_im.shape[1], nmb_channels)
    c_histograms = [np.histogram(im[:,_], bins=nmb_bins,
            density=USE_DENSITY, range=(0, 255))[0] for _ in range(nmb_channels)]
    if nmb_channels == 1:
      # propagate single channel histogram values into rgb channels
      c_histograms = c_histograms * 3
    histograms_for_bin_numbers.append(np.array(list(chain.from_iterable(c_histograms))))

  return np.array(histograms_for_bin_numbers)


if __name__ == '__main__':
  print get_flat_list_histogram_for_image_path(TEST_IMAGE_PATH, [4,3,2,1])
