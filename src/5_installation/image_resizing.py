import tempfile
import os
from skimage.io import imread, imsave
from skimage.transform import resize

def resize_image_to_width(src_file_path, width_size):
  # create temporary directory
  tmp_resized_img_dir = tempfile.mkdtemp()
  # get incoming file name only
  _, dest_resized_file_name = os.path.split(src_file_path)
  # generate new path in temporary directory
  dest_resized_file_path = os.path.join(tmp_resized_img_dir, dest_resized_file_name)

  im = imread(src_file_path)
  width = im.shape[1]
  ratio = width / float(width_size)
  im = resize(im, (int(im.shape[0] / ratio), int(width_size)), anti_aliasing=True, mode='constant')
  imsave(dest_resized_file_path, im)

  return dest_resized_file_path

def resize_image_for_vectorization(src_file_path):
  return resize_image_to_width(src_file_path, 512)
