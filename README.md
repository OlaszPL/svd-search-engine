# SVD Search Engine 🔍

SVD Search Engine to silnik wyszukiwania wykorzystujący metodę Singular Value Decomposition (SVD) do analizy i wyszukiwania podobnych artykułów. Dzięki redukcji wymiarowości oraz ekstrakcji kluczowych cech tekstu, umożliwia efektywne porównywanie treści. System operuje na wektorach cech typu _bag_of_words_, które odzwierciedlają częstość występowania słów kluczowych w artykułach.

Rozwiązanie pozwala na przeszukiwanie artykułów pochodzących z dowolnego zrzutu danych z _Wikipedii_ (w formacie _.xml_).

![](img/front.png)

## Użytkowanie

### Wymagania techniczne

- Python 3.13+
- Biblioteki: _numpy, hnswlib, nltk, scikit-learn, streamlit, tqdm_

> [!IMPORTANT]
> Wiele operacji stosowanych w wyszukiwarce intenstywnie korzysta z zasobów pamięci operacyjnej, dlatego zalecane jest ponad 16GB pamięci RAM (w szczególnośći dla dużej liczby _k_ stosowanej w SVD).

### Wymagania wstępne

**1. Sklonuj repozytorium:**
```bash
git clone https://github.com/OlaszPL/svd-search-engine.git
```

**2. Przejdź do katalogu z kodem źródłowym:**
```bash
cd svd-search-engine
```

**3. Upewnij się, że masz zainstalowane wymagane biblioteki. Można je zainstalować za pomocą pliku `requirements.txt`:**
```bash
pip install -r requirements.txt
```

### Przygotowanie danych

**1. Pobierz dowolny zrzut danych z Wikipedii (w języku angielskim) [z tej strony](https://dumps.wikimedia.org/backup-index.html), np. zrzut [_simple_english_](https://dumps.wikimedia.org/simplewiki/20250420/simplewiki-20250420-pages-articles-multistream.xml.bz2) (w formacie _.xml.bz2_).**

**2. Przejdź do folderu ``data``, wypakuj pobrane archiwum do folderu ``input``, zmień nazwę pliku na ``wiki.xml``. Następnie uruchom:**
```bash
python ./create_wiki_db.py
```
Zaczekaj na utworzenie bazy danych.

**3. Uruchom tworzenie _bag_of_words_, a następnie _term_by_document_:**
```bash
python ./bag_of_words.py

python ./term-by-document.py
```

>[!NOTE]
> Obie operacje wymagają czasu na inicjalizację procesów oraz przetworzenie wszystkich artykułów.