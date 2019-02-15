import os
from collections import defaultdict

all_weights = defaultdict(int)
all_weights.update({"ahash":"0.787","dhash":'1.102',"hist":17.008,"hist_ahash":0.630,
  "hist_dhash":0.630,"hist_phash":12.441,"hist_whash":0.945,"image_ratio":1.102,
  "lines_angle_hist":5.512,"lines_horiz_dist_hist":3.622,"lines_vert_dist_hist":3.622,
  "multi_hist":6.772,"phash":3.150,"tf":20.000,"whash":0.787})

for k,v in all_weights.iteritems():
	all_weights[k]=float(v)
print all_weights

# global_transfer_value = 2.833434

# e =[(_, '%.1f' % (_/10.0) ** global_transfer_value) for _ in range(10)]

# print e

# for _ in range(10):
# 	print _
# 	print '%.1f' % (_/10.0)
# 	print '%.1f' % (_/10.0) ** global_transfer_value

