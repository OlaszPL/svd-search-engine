import sqlite3
import nltk
import concurrent.futures
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from string import punctuation
from tqdm import tqdm

############################################
# Creation of terms set
############################################

# specifies terms as a union of all words from every article, then does preprocessing:
# 1. stemming
# 2. stop words removal
# these two steps will be done when words will be read

# Output -> set of terms

def preprocess(db_path : str, lang : str):
    stop_words = set(stopwords.words(lang)) | set(punctuation)
    conn = sqlite3.connect(db_path)
    terms = set()

    ps = PorterStemmer()
    c = conn.cursor()

    for row in tqdm(c.execute("SELECT text FROM articles")):
        text = row[0]
        if text:
            tokens = word_tokenize(text)
            terms.update(
                word for word in (ps.stem(token, to_lowercase = True) for token in tokens) # to lowercase and stem
                if word not in stop_words # stop words omitted
            )

    conn.close()

    return terms


if __name__ == "__main__":
    nltk.download('stopwords')
    nltk.download('punkt_tab')

    terms = preprocess("./wiki.db", "english")
    print(len(terms))