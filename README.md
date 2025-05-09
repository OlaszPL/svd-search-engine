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

Plik _.xml_ parse'owany jest przy pomocy [mojego forka](https://github.com/OlaszPL/wikiextractor/) biblioteki _wikiextractor_, gdzie naprawiłem wsparcie dla Pythona 3.13, systemu Windows, funkcjonowanie zapisu do plików _json_ oraz przetwarzanie list punktowanych. Pakiet został zamieszczony w folderze `data`, nie trzeba podejmować dodatkowych kroków.

**3. Uruchom tworzenie _bag_of_words_, a następnie _term_by_document_:**
```bash
python ./bag_of_words.py

python ./term-by-document.py
```

>[!NOTE]
> Obie operacje wymagają czasu na inicjalizację procesów oraz przetworzenie wszystkich artykułów.

## Uruchamianie aplikacji

**Przejdź do katalogu głównego a następnie wywołaj:**
```bash
streamlit run main.py
```

Wybranie przy pomocy suwaka _k_ utworzy SVD dla macierzy oraz indeks HNSW. Czynność ta jest jednorazowa dla wybranego k (pliki są zapisywane w katalogu `data/objects/SVD`).

## Rozwiązania przyjęte podczas implementacji

### Pozyskiwane dane

Dane pochodzą z oficjalnych zrzutów Wikipedii w formacie _.xml_ (do testów skorzystałem z _simplewiki_). Plik _.xml_ parse'owany jest przy pomocy [mojego forka](https://github.com/OlaszPL/wikiextractor/) biblioteki _wikiextractor_, gdzie naprawiłem wsparcie dla Pythona 3.13, systemu Windows, funkcjonowanie zapisu do plików _json_ oraz przetwarzanie list punktowanych. Następnie tworzona jest baza danych SQLite - dla wygodnego dostępu w późniejszych etapach przetwarzania.

### Utworzenie zbioru słów _bag_of_words_

Artykuły przetwarzam wieloprocesowo z wykorzystaniem ``ProcessPoolExecutor``. Tekst każdego z artykułów jest tokenizowany przy pomocy ``word_tokenize`` z biblioteki ``nltk``. Następnie każde ze słów jest sprowadzane do rdzenia przy pomocy algorytmu ``PorterStemmer`` (jednocześnie przetwarzane są do małych liter) oraz dodawane do zbioru słów o ile nie jest zawarte w zbiorze ``stopwords``. Zbiór ten jest unią terminów wczytanych z pliku tekstowego, z biblioteki ``nltk`` oraz znaków interpunkcyjnych. Finalnie zapisywany jest słownik mapujący słowa na kolejne indeksy.

### Budowanie macierzy z wektorów _term_by_document_

Proces jest podobny do generowania zbioru _bag_of_words_ z tą różnicą, że tym razem dla każdego z artykułów tworzony jest słownik, który dla każdego indeksu słowa (indeksy pochodzą ze słownika mapującego) zlicza liczbę jego wystąpień w całym tekście. Następnie na podstawie tych słowników buduje się macierz rzadką (``csr``) zawierającą wektory wystąpień słów dla każdego z artykułów.

Następnie przy pomocy ``TfidfTransfmormer`` aplikowane są TF-IDF (Term Frequency–Inverse Document Frequency) oraz normalizacja w normie _l2_. Wykorzystanie TF-IDF pomaga tutaj: 

+ Wyróżnić istotne słowa – podnosi wagę słów, które często występują w danym dokumencie, ale rzadko w innych.
+ Redukować wpływ popularnych słów – obniża wagę słów bardzo często występujących w całym korpusie (np. "i", "oraz", "the"), które nie niosą istotnej informacji.

Finalnie macierz zapisywana jest do pliku.

### SVD

Istnieje możliwość opcjonalnego usunięcia szumu z macierzy A poprzez SVD (Singular Value Decomposition) i low rank approximation. Po ustawieniu preferowanej wartości ``k`` tworzone jest SVD przy pomocy bibliotecznej funkcji ``TruncatedSVD``, która dostosowana jest do macierzy rzadkich, na których zastosowano TF-IDF. Bardzo dobrze redukuje tutaj wymiarowość. Wygenerowana macierz jest zapisywana do późniejszego wykorzystania.

### Wyszukiwanie

Wyszukiwanie rozpoczyna się od przetworzenia wprowadzonego tekstu w wektor o identycznej postaci co te umieszczone w macierzy (w przypadku wykorzystania macierzy z SVD wektor jest dodatrkowo transformowany).

Następnie wyszukiwanie odbywać się może na 2 sposoby:

1. Z wykorzystaniem wartości _cosinusa_ między wektorami oraz posortowaniem malejąco poprzez ``np.argsort``,
2. Przy pomocy ANN (Approximate Nearest Neighbors) z wykorzystaniem bibliotecznego algorytmu HNSW (Hierarchical Navigable Small World). Ze względu na dostępne zasoby systemowe, ANN można zastosować tylko na macierzach z SVD. Indeks _hnswlib_ tworzony jest podczas generowania SVD i wczytywany po utworzeniu obiektu ``Search``.

### Frontend

Frontent wyszukiwarki napisany został z wykorzystaniem frameworka ``streamlit``.

## Porównanie działania programu bez usuwania szumu i z usuwaniem szumu - dla różnych wartości ``k``