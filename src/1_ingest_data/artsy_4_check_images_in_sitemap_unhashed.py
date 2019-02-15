import pickle

SITEMAP_DATA_PICKLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_sitemaps.pickle'

print 'loading SITEMAP_DATA_PICKLE_PATH'
with open(SITEMAP_DATA_PICKLE_PATH) as f:
  all_sitemap_data = pickle.load(f)

print len(all_sitemap_data)


HASHES_DATA_PICKLE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/1_ingest_data/serialized_data/artsy_hashes.pickle'

print 'loading HASHES_DATA_PICKLE_PATH'
with open(HASHES_DATA_PICKLE_PATH) as f:
  all_hashes_data = pickle.load(f)

print len(all_hashes_data)

"""

NOT DOING ANYTHING about discrepancy as sitemap has 823158 entries, and hash has 823151 entries...!!!!

perfect + good + onwards (i.e., no need to find out/process the missing 7 entries.....!)

"""