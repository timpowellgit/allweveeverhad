import imageio
import numpy
import tensorflow as tf
from tensorflow_classify_image import run_inference_on_image_data
import sys
import scipy
from scipy import spatial


def generate_tf(all_ids_to_image_paths, graph_path):
  return run_inference_on_image_data(
      all_ids_to_image_paths=all_ids_to_image_paths,
      graph_path=graph_path)

if __name__ == '__main__':
  v1 = generate_tf(sys.argv[1])
  v2 = generate_tf(sys.argv[2])
  print 'distance',scipy.spatial.distance.cdist([v1], [v2])
