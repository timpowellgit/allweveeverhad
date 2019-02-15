# Load libraries
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
from sklearn import datasets
import numpy as np

# Load the data
digits = datasets.load_digits()

print('digits.data.shape', digits.data.shape)

print('digits.data', digits.data)
print('digits.data.shape', digits.data.shape)

# Standardize the feature matrix
X = StandardScaler().fit_transform(digits.data)

# Make sparse matrix
X_sparse = csr_matrix(X)

# Create a TSVD
tsvd = TruncatedSVD(n_components=10, random_state=162954531)

# Conduct TSVD on sparse matrix
X_sparse_tsvd = tsvd.fit(X_sparse)

print('X_sparse_tsvd.components_.shape', X_sparse_tsvd.components_.shape)

# at this point, GET/SET components_, which will be n_components * n_original_vectors shape
# LATER
# LATER
# LATER
# LATER
# LATER

X_sparse_tsvd = X_sparse_tsvd.transform(np.array([range(64)]))

print('X_sparse_tsvd', X_sparse_tsvd)

# Show results
print('Original number of features:', X_sparse.shape[1])
print('Reduced number of features:', X_sparse_tsvd.shape[1])

# Sum of first three components' explained variance ratios
print tsvd.explained_variance_ratio_[:10].sum()
