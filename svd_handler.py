import os
import pickle
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

def give_svd_path(k):
    os.makedirs("./data/objects/SVD", exist_ok = True)
    svd = TruncatedSVD(n_components = k)

    matrix_filename = f"matrix_SVD_{k}.pkl"
    model_filename = f"matrix_SVD_{k}_model.pkl"

    if os.path.isfile(f"./data/objects/SVD/{matrix_filename}")and os.path.isfile(f"./data/objects/SVD/{model_filename}"):
        with open(f"./data/objects/SVD/{model_filename}", "rb") as f:
            svd = pickle.load(f)
        return svd, matrix_filename
    else:
        # create svd matrix
        print(f"Performing new SVD for k = {k}...")

        with open(f"./data/objects/matrix.pkl", "rb") as f:
            A = pickle.load(f)
            A : csr_matrix

        A_k = svd.fit_transform(A.T) # temporary change to (n x m)
        A_k = A_k.T # now (k x n)

        with open(f"./data/objects/SVD/{matrix_filename}", "wb") as f:
            pickle.dump(A_k, f)
        with open(f"./data/objects/SVD/{model_filename}", "wb") as f:
            pickle.dump(svd, f)

    return svd, matrix_filename

if __name__ == "__main__":
    give_svd_path(32)