from annoy import AnnoyIndex
import pickle
from tqdm import tqdm

NMB_ANNOY_TREES = 25
HISTOGRAM_INPUT_PICKLES_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/complete_histograms.pickle-pandas'
ANNOY_OUTPUT_FILES_TEMPLATE = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/annoy_data/{}.ann'

print 'loading histogram data from pickles file'
with open(HISTOGRAM_INPUT_PICKLES_PATH) as f:
  histogram_data = pickle.load(f)

print 'found cols', list(histogram_data)
for col_name in tqdm(histogram_data, desc="hist cols"):
  col = histogram_data[col_name]
  nmb_vectors = len(col.iloc[0])
  t = AnnoyIndex(nmb_vectors, metric='euclidean')
  for idx in tqdm(col.index, desc="col row"):
    t.add_item(idx, col[idx])
  t.build(NMB_ANNOY_TREES)

  output_ann_file_path = ANNOY_OUTPUT_FILES_TEMPLATE.format(col_name)
  t.save(output_ann_file_path)
