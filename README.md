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

Testy przeprowadzono dla zrzutu _simplewiki_, z którego zgromadzono **266054** artykuły, których korpus zawiera **775682** słów (nie usuwano słów występujących rzadko, gdyż wykorzystano macierz rzadką oraz TF-IDF).

Wyszukiwania bez SVD przeprowadzono dla cosinusa a z SVD dla ANN.


### Fraza: "bloody battle in middle ages"

| Pozycja | Bez SVD                                      | SVD k = 128               | SVD k = 256                     | SVD k = 384                | SVD k = 512                | SVD k = 640                   |
|---------|-----------------------------------------------|-------------------------|-------------------------------|--------------------------|--------------------------|------------------------------|
| 1       | Middle Ages (0.5086)                          | Bertolt Brecht (0.8535)   | Age (0.8111)          | Battle (0.6821)      | Battle (0.6983)      | Age (0.6324)         |
| 2       | Early Middle Ages (0.4263)                           | Illuminated manuscript (0.8011)     | 820 (0.7279)      | Battle of Bosworth Field (0.6674)     | Battle of Bosworth Field (0.6887)     | Age of consent (0.5401)     |
| 3       | Battle (0.4060)                          | Petros Duryan (0.7801)    | High Middle Ages (0.6766)      | Battle of Poitiers (0.6600) | Battle of Poitiers (0.6755) | Early Middle Ages (0.5072)         |
| 4       | Middle age (0.3915)                       | 820 (0.7705)| Tweenager (0.6388)        | Battle of Yorktown (0.6585) | Battle of Yorktown (0.6721)     | Middle age (0.4731)      |
| 5       | High Middle Ages (0.3766)             | High Middle Ages (0.7649)      | Bajocian (0.6283)         | Pyrrhic victory (0.6484)  | Tactical victory (0.6688)  | High Middle Ages (0.4565)       |
| 6       | Battle of Mine Creek (0.3715)                     | List of last surviving World War I veterans by country (0.6866)     | Reu (0.6283)          | Tactical victory (0.6412)   | Battle of Polygon Wood (0.6565)   | Bajocian (0.4483)        |
| 7       | Bloody Sunday (0.3434)| Tallit (0.6662)   | Serug (0.5966)   | Battle of Polygon Wood (0.6325)    | Bulge (0.6525)    | Three-age system (0.4314) |
| 8       | Battle of Perryville (0.3371)                 | Bajocian (0.6644)    | Three-age system (0.5862)          | Bulge (0.6273)     | Campaign of Danture (1594) (0.6497)     | Presbyopia (0.4192)          |
| 9       | Battle of Hastings (0.3370)                    | Three-age system (0.6638)    | Presbyopia (0.5853)        | Campaign of Danture (1594) (0.6227)   | Battle of Svolder (0.6342)   | Isaac ben Moses of Vienna (0.3990)        |
| 10      | Battle of Amiens (1918) (0.3311)                         | Presbyopia (0.6592)   | Theodoric Borgognoni (0.5789)               | Battle of Svolder (0.6213)          | Battle of Al Rahlayn (0.6340)          | Theodoric Borgognoni (0.3868)              |

### Fraza: "Donald Trump"

| Pozycja | Bez SVD                                      | SVD k = 128               | SVD k = 256                     | SVD k = 384                | SVD k = 512                | SVD k = 640                   |
|---------|-----------------------------------------------|-------------------------|-------------------------------|--------------------------|--------------------------|------------------------------|
| 1       | The Trump Organization (0.8674)                          | Kamala Harris (0.9938)   | Donald Trump 2016 presidential campaign (0.9963)          | Donald Trump 2016 presidential campaign (0.9980)      | The Trump Organization (0.9988)      | Ivana Trump (0.9988)         |
| 2       | Trump (0.8514)                           | Donald Trump 2016 presidential campaign (0.8605)     | The Trump Organization (0.9053)      | The Trump Organization (0.9469)     | Trump (0.9671)     | The Trump Organization (0.9741)     |
| 3       | Eric Trump (0.7643)                          | First inauguration of Donald Trump (0.8382)    | Trump (0.8792)      | Trump (0.9302) | Eric Trump (0.9574) | Trump (0.9597)         |
| 4       | Donald Trump (0.7542)                       | First presidency of Donald Trump (0.8022)| Protests against Donald Trump (0.7915)        | Trump Tower (0.8766) | Donald Trump (disambiguation) (0.9102)     | Donald Trump (disambiguation) (0.9217)      |
| 5       | Impeachment of Donald Trump (0.7455)             | Impeachment of Donald Trump (0.7941)      | Donald Trump 2020 presidential campaign (0.7481)         | Donald Trump (disambiguation) (0.8580)  | Impeachment of Donald Trump (0.9083)  | Impeachment of Donald Trump (0.9187)       |
| 6       | Family of Donald Trump (0.7340)                     | Joe Biden 2024 presidential campaign (0.7925)     | Impeachment of Donald Trump (0.7201)          | Impeachment of Donald Trump (0.8411)   | Family of Donald Trump (0.9067)   | Family of Donald Trump (0.9184)        |
| 7       | Never Trump movement (0.7241)| Family of Donald Trump (0.7923)   | Family of Donald Trump (0.7165)   | Family of Donald Trump (0.8057)    | Never Trump movement (0.8943)    | Never Trump movement (0.9061) |
| 8       | Inauguration of Donald Trump (0.7139)                 | Donald Trump 2024 presidential campaign (0.7909)    | Never Trump movement (0.7152)          | Never Trump movement (0.7511)     | Inauguration of Donald Trump (0.8388)     | Inauguration of Donald Trump (0.8687)          |
| 9       | Attempted assassination of Donald Trump (0.6967)                    | Inauguration of Donald Trump (0.7854)    | 2024 United States presidential debates (0.7135)        | Inauguration of Donald Trump (0.7349)   | Attempted assassination of Donald Trump (0.8193)   | Attempted assassination of Donald Trump (0.8512)        |
| 10      | Presidency of Donald Trump (0.6709)                         | Second presidency of Donald Trump (0.7846)   | Inauguration of Donald Trump (0.7030)               | Attempted assassination of Donald Trump (0.7318)          | Presidency of Donald Trump (0.8146)          | Presidency of Donald Trump (0.8445)              |

### Fraza: "the most renowned discrete mathematicians of all time"

| Pozycja | Bez SVD                                      | SVD k = 128               | SVD k = 256                     | SVD k = 384                | SVD k = 512                | SVD k = 640                   |
|---------|-----------------------------------------------|-------------------------|-------------------------------|--------------------------|--------------------------|------------------------------|
| 1       | Time zone (0.4299)                          | Coordinated Universal Time (0.9937)   | Coordinated Universal Time (0.9955)          | Coordinated Universal Time (0.9917)      | Coordinated Universal Time (0.9841)      | Coordinated Universal Time (0.9768)         |
| 2       | Standard time (0.3771)                           | Stopwatch (0.9804)     | Stopwatch (0.9853)      | Standard time (0.9714)     | Time zone (0.9508)     | Time zone (0.9381)     |
| 3       | Ecclesiastes (0.3338)                          | Time domain (0.9636)    | Time domain (0.9814)      | Time domain (0.9689) | Standard time (0.9469) | Greenwich Mean Time (0.9325)         |
| 4       | National Hockey League All-Star Game (0.3106)                       | Nepal Standard Time (0.9488)| Nepal Standard Time (0.9646)        | Time in Kazakhstan (0.9543) | Time domain (0.9420)     | Standard time (0.9108)      |
| 5       | Discrete mathematics (0.3054)             | Time in Kazakhstan (0.9217)      | Time in Kazakhstan (0.9528)         | Hawaii–Aleutian Time Zone (0.9381)  | Time in Kazakhstan (0.9258)  | Time domain (0.9065)       |
| 6       | Time domain (0.2987)                     | Israel Standard Time (0.9062)     | Hawaii–Aleutian Time Zone (0.9473)          | Time in Vietnam (0.9371)   | Time in Vietnam (0.9168)   | Time in Kazakhstan (0.9060)        |
| 7       | Discrete (0.2952)| Hong Kong Time (0.8996)   | Alaska Standard Time (0.9434)   | Time in India (0.9236)    | Time in India (0.9166)    | Hawaii–Aleutian Time Zone (0.8749) |
| 8       | Moscow Time (0.2874)                 | Alaska Standard Time (0.8819)    | Time in Vietnam (0.9429)          | Bhutan Time (0.9232)     | Bhutan Time (0.9012)     | Time in India (0.8656)          |
| 9       | Time in India (0.2719)                    | Time in Vietnam (0.8811)    | Kyrgyzstan Time (0.9395)        | Kyrgyzstan Time (0.9163)   | Kyrgyzstan Time (0.8942)   | Bhutan Time (0.8653)        |
| 10      | Wright Renown (0.2633)                         | Depreciation (0.8761)   | Depreciation (0.9395)               | Depreciation (0.9149)          | Depreciation (0.8896)          | Kyrgyzstan Time (0.8577)              |