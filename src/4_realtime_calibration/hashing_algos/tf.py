import imageio
import numpy
import tensorflow as tf
from tensorflow_classify_image import run_inference_on_image_data
import sys
import scipy
from scipy import spatial
import os

GRAPH_DATA_PATH = os.environ['TENSORFLOW_GRAPH_PATH']

def generate_tf(image_path):
  image_data = tf.gfile.FastGFile(image_path, 'rb').read()
  return run_inference_on_image_data(graph_path=GRAPH_DATA_PATH, image_data=image_data)

if __name__ == '__main__':
  v1 = generate_tf(sys.argv[1])
  v2 = generate_tf(sys.argv[2])
  print 'distance',scipy.spatial.distance.cdist([v1], [v2])
