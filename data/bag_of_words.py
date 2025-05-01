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
# these two steps will be done when words are be read

# Output -> set of terms

STOP_WORDS = None

def init_worker(stop_words):
    global STOP_WORDS
    STOP_WORDS = stop_words

def process_text(text): # for multiple processes
    ps = PorterStemmer()
    if text:
        tokens = word_tokenize(text)
        return {
            word for word in (ps.stem(token, to_lowercase = True) for token in tokens) # to lowercase and stem
            if word not in STOP_WORDS # stop words omitted
        }

    return set()
        
def preprocess(db_path : str, lang : str):
    stop_words = set(stopwords.words(lang)) | set(punctuation)
    conn = sqlite3.connect(db_path)
    terms = set()

    c = conn.cursor()
    texts = [row[0] for row in c.execute("SELECT text FROM articles")]
    conn.close()

    with concurrent.futures.ProcessPoolExecutor(
        initializer = init_worker, initargs = (stop_words,)
    ) as executor:
        for term_set in tqdm(executor.map(process_text, texts), total = len(texts)):
            terms.update(term_set)

    return terms


def main(db_path, lang):
    terms = preprocess(db_path, lang)
    print(len(terms))


if __name__ == "__main__":
    nltk.download('stopwords')
    nltk.download('punkt_tab')

    main("./wiki.db", "english")