import sys
from get_image_size import get_image_metadata
import numpy as np

def generate_image_ratio(image_path):
  try:
    img_data = get_image_metadata(image_path)
  except:
    return None
  return np.array([img_data.width/float(img_data.height)])

if __name__ == '__main__':
  print generate_image_ratio(sys.argv[1])
