import sqlite3
import pickle
import hnswlib
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from scipy.sparse import csr_matrix
from enum import Enum
from sklearn.preprocessing import normalize

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

        match k:
            case 0: matrix_path = "matrix.pkl"

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

        q = normalize(q, norm = 'l2', axis = 1) # l2 normalization

        return q.T # vertical matrix
    
    def search(self, text : str, mode : Mode, number):
        q = self._prepare_query_vector(text)
        q : csr_matrix

        if mode == Mode.COSINE:
            similarities = abs(q.T @ self.A)
            similarities : csr_matrix
            arr = similarities.toarray()
            top_k_idx = np.argsort(arr[0])[::-1][:number]

            res = [(int(idx) + 1, arr[0, idx]) for idx in top_k_idx] # reindex for sql

            return res

        else:
            if self.k < 50:
                print("Too low k to use ANN!")
                return []
            if not self.p: # only works with particular SVD
                self.p = hnswlib.Index(space = 'cosine', dim = len(Search.term_to_index))
                self.p.init_index(max_elements = self.A.shape[1])
                self.p.set_ef(50)
                self.p.add_items(self.A)
            else:
                indices, distances = self.p.knn_query(q, number)

                res = [(int(idx) + 1, distance) for idx, distance in zip(indices, distances)] # reindex

                return res
        
    
if __name__ == "__main__":
    s = Search()
    conn = sqlite3.connect("./data/wiki.db")
    
    while True:
        query = input("Enter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            conn.close()
            break

        res = s.search(query, Mode.COSINE, 10)

        cursor = conn.cursor()
        placeholders = ','.join(['?'] * len(res))
        query = f"SELECT title, url FROM articles WHERE id IN ({placeholders})"
        cursor.execute(query, [idx for idx, _ in res])
        db_query = cursor.fetchall()
        for (_, match), (title, url) in zip(res, db_query):
            print(f"{title} - {url} | match = {match:.4f}")
        print()