import pickle
import os
import pandas as pd

DIR = '/Users/greg/Desktop/blacklist pickle'

blacklist = []

filepaths = [_ for _ in os.listdir(DIR) if _.endswith('.pickle')]
for filepath in filepaths:
  with open(os.path.join(DIR, filepath)) as f:
    data = pickle.load(f)
  blacklist.extend(list(data))
print blacklist