from annoy import AnnoyIndex

NMB_VECTORS = 3
NMB_TREES = 10
ANNOY_FILE_PATH = '/tmp/test.ann'

t = AnnoyIndex(NMB_VECTORS, metric='euclidean')
t.add_item(0, [15, 20, 30])
t.add_item(0, [10, 20, 30])
t.add_item(0, [15, 20, 30])
t.build(NMB_TREES)
t.save(ANNOY_FILE_PATH)

u = AnnoyIndex(NMB_VECTORS, metric='euclidean')
u.load(ANNOY_FILE_PATH)
print u.get_nns_by_vector([15, 20, 30], 2, include_distances=True)

# yep, no problem adding item with same index as before......!