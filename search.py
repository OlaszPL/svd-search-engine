import sqlite3
import pickle
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

    ps = PorterStemmer()

    def __init__(self, k = 0):
        match k:
            case 0: matrix_path = "matrix.pkl"

        with open(f"./data/objects/{matrix_path}", "rb") as f:
            self.A = pickle.load(f)

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
            res = similarities.toarray()
            res : np.ndarray
            top_k_idx = np.argsort(res[0])[::-1][:number]

            conn = sqlite3.connect("./data/wiki.db")
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(top_k_idx))
            query = f"SELECT title, url FROM articles WHERE id IN ({placeholders})"
            cursor.execute(query, [int(idx) + 1 for idx in top_k_idx])
            results = cursor.fetchall()
            conn.close()
            for idx, (title, url) in zip(top_k_idx, results):
                print(f"{title} - {url} | cos = {res[0][idx]:.4f}")

        else:
            raise NotImplemented
        
    
if __name__ == "__main__":
    s = Search()
    while True:
        query = input("Enter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        s.search(query, Mode.COSINE, 10)