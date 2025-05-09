import os
import pickle
import hnswlib
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

def give_svd_path(k):
    os.makedirs("./data/objects/SVD", exist_ok = True)
    svd = TruncatedSVD(n_components = k)

    matrix_filename = f"matrix_SVD_{k}.pkl"
    model_filename = f"matrix_SVD_{k}_model.pkl"
    index_filename = f"matrix_SVD_{k}_index.pkl"

    if os.path.isfile(f"./data/objects/SVD/{matrix_filename}")and os.path.isfile(f"./data/objects/SVD/{model_filename}"):
        with open(f"./data/objects/SVD/{model_filename}", "rb") as f:
            svd = pickle.load(f)
        return svd, matrix_filename, index_filename
    else:
        # create svd matrix
        print(f"Performing new SVD for k = {k}...")

        with open(f"./data/objects/matrix.pkl", "rb") as f:
            A = pickle.load(f)
            A : csr_matrix

        A_k = svd.fit_transform(A.T) # temporary change to (n x m)
        A_k_T = A_k.T # now (k x n)

        with open(f"./data/objects/SVD/{matrix_filename}", "wb") as f:
            pickle.dump(A_k_T, f)
        with open(f"./data/objects/SVD/{model_filename}", "wb") as f:
            pickle.dump(svd, f)

        print("Initializing hnsw index...")

        index = hnswlib.Index(space = 'cosine', dim = A_k.shape[1])
        index.init_index(max_elements = A_k.shape[0])
        index.set_ef(50)
        index.add_items(A_k)
        index.save_index(f"./data/objects/SVD/{index_filename}")

    return svd, matrix_filename, index_filename

if __name__ == "__main__":
    give_svd_path(512)