import sqlite3
import concurrent.futures
import pickle
import os
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfTransformer
from tqdm import tqdm

############################################
# Creation of term-by-document matrix
############################################

# 1. create vector d for every file
# 2. compose vectors d into term-by-document matrix, as for now rows - documents, columns - terms, later will be transposed
# 3. TF-IDF
# 4. transpose matrix to bo in the format said by paper
# 5. de noising

TERM_TO_INDEX = None

def init_worker(term_to_index):
    global TERM_TO_INDEX
    TERM_TO_INDEX = term_to_index

def process_text(text): # for multiple processes
    ps = PorterStemmer()
    if text:
        tokens = word_tokenize(text)
        count = {}

        for token in tokens:
            word = ps.stem(token, to_lowercase = True)
            if word in TERM_TO_INDEX:
                count[TERM_TO_INDEX[word]] = count.get(TERM_TO_INDEX[word], 0) + 1

        return count

    return {}


def create_matrix(db_path : str):
    with open("./objects/term_to_index.pkl", "rb") as f:
        term_to_index = pickle.load(f)

    conn = sqlite3.connect(db_path)
    
    rows = []
    cols = []
    cnts = []

    c = conn.cursor()
    texts = [row[0] for row in c.execute("SELECT text FROM articles")]
    conn.close()

    with concurrent.futures.ProcessPoolExecutor(
        initializer = init_worker, initargs = (term_to_index,)
    ) as executor:
        for row, vector in enumerate(tqdm(executor.map(process_text, texts), total = len(texts))):
            for col, cnt in vector.items():
                rows.append(row)
                cols.append(col)
                cnts.append(cnt)

    A = csr_matrix((cnts, (rows, cols)), shape=(len(texts), len(term_to_index)))
    # (n x m) as for now

    return A


def process_matrix(A_bare : csr_matrix):
    t = TfidfTransformer() # applies TF-IDF and normalize matrix
    # default=‘l2’: Sum of squares of vector elements is 1. The cosine similarity between two vectors is their dot product when l2 norm has been applied.
    A = t.fit_transform(A_bare)

    return A.T # now it's (m x n), according to the paper


def main(db_path):
    A = process_matrix(create_matrix(db_path)) # (m x n)

    os.makedirs("./objects", exist_ok = True)
    with open("./objects/matrix.pkl", "wb") as f:
        pickle.dump(A, f)

    print("Matrix successfully saved!")


if __name__ == "__main__":
    main("./wiki.db")