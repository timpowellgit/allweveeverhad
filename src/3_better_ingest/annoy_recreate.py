from annoy import AnnoyIndex
from tqdm import tqdm
import numpy as np

def recreate_annoy_index(nmb_trees, nmb_vectors, metric,
  curr_annoy_file_path, new_annoy_file_path,
  keep_vector_ids, new_vectors):

  existing_index = AnnoyIndex(nmb_vectors, metric=metric)
  existing_index.load(curr_annoy_file_path)
  new_index = AnnoyIndex(nmb_vectors, metric=metric)

  for keep_vector_id in tqdm(keep_vector_ids, desc='copying existing annoy row'):
    try:
      existing_vector = existing_index.get_item_vector(keep_vector_id)
    except IndexError:
      # it's possible for the index to exist in the database but for the vector
      # to not exist in the annoyfile
      # example: images processed by the hough lines algo will not have a corresponding
      # vector in the angle/horiz/vert indices if no lines were detected (or only
      # horiz or vert lines were detected)
      continue

    assert np.array(existing_vector).dtype == np.float64, 'not float64, vector id {}'.format(keep_vector_id)
    assert len(existing_vector) == nmb_vectors, 'len of vector is not nmb_vectors, vector id {}'.format(keep_vector_id)

    new_index.add_item(keep_vector_id, existing_vector)

  existing_index.unload()

  for new_vector_key, new_vector_val in tqdm(new_vectors.items(), desc='adding new annoy rows'):
    new_index.add_item(new_vector_key, new_vector_val)

  print 'building index'
  new_index.build(nmb_trees)

  print 'saving index'
  new_index.save(new_annoy_file_path)

  print 'done, unloading'
  new_index.unload()
  print 'unloaded'
