import sqlite3
import pickle
import hnswlib
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from scipy.sparse import csr_matrix
from enum import Enum
from sklearn.preprocessing import normalize
from svd_handler import give_svd_path

class Mode(Enum):
    COSINE = 0
    ANN = 1
    

class Search():
    with open("./data/objects/term_to_index.pkl", "rb") as f:
        term_to_index = pickle.load(f) # static attribute
        term_to_index : dict

    ps = PorterStemmer()

    def __init__(self, k = 0):
        self.k = k
        self.svd = None

        match k:
            case 0:
                matrix_path = "matrix.pkl"
            case _ if k > 0:
                self.svd, matrix_name = give_svd_path(k)
                matrix_path = f"SVD/{matrix_name}"
            case _:
                raise ValueError(f"Unsupported value for k: {k}")

        with open(f"./data/objects/{matrix_path}", "rb") as f:
            self.A = pickle.load(f)
            self.A : csr_matrix

        self.p = None

    def _prepare_query_vector(self, text : str):
        terms = [Search.ps.stem(word, to_lowercase = True) for word in word_tokenize(text)]
        count = {}

        for term in terms:
            if term in Search.term_to_index:
                count[Search.term_to_index[term]] = count.get(Search.term_to_index[term], 0) + 1

        cnts = list(count.values())
        indices = list(count.keys())

        q = csr_matrix(
            (cnts, ([0] * len(cnts), indices)),
            shape=(1, len(Search.term_to_index))
        )

        if self.svd is not None:
            q = self.svd.transform(q)

        q = normalize(q, norm = 'l2', axis = 1) # l2 normalization

        return q.T # vertical matrix
    
    def search(self, text : str, mode : Mode, number):
        q = self._prepare_query_vector(text)
        q : csr_matrix

        if mode == Mode.COSINE:
            similarities = abs(q.T @ self.A)

            if isinstance(similarities, csr_matrix):
                arr = similarities.toarray()
            else:
                arr = similarities
            
            top_k_idx = np.argsort(arr[0])[::-1][:number]

            res = [(int(idx) + 1, arr[0, idx]) for idx in top_k_idx] # reindex for sql

            return res

        else:
            if self.k == 0:
                print("SVD is needed to use ANN!")
                return []
            if self.p is None: # only works with particular SVD
                self.p = hnswlib.Index(space = 'cosine', dim = self.A.shape[0])
                self.p.init_index(max_elements = self.A.shape[1])
                self.p.set_ef(50)
                self.p.add_items(self.A.T)

            indices, distances = self.p.knn_query(q.T, number)
            res = [(int(idx) + 1, 1 - distance) for idx, distance in zip(indices[0], distances[0])] # reindex

            return res
        
    
if __name__ == "__main__":
    s = Search(512)
    conn = sqlite3.connect("./data/wiki.db")
    
    while True:
        query = input("Enter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            conn.close()
            break

        res = s.search(query, Mode.ANN, 10)

        cursor = conn.cursor()
        placeholders = ','.join(['?'] * len(res))
        query = f"SELECT title, url FROM articles WHERE id IN ({placeholders})"
        cursor.execute(query, [idx for idx, _ in res])
        db_query = cursor.fetchall()
        for (_, match), (title, url) in zip(res, db_query):
            print(f"{title} - {url} | match = {match:.4f}")
        print()