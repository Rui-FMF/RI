# RI - Assignment 2

This assignment consisted in extending the indexer developed in assignment 1 with weighted indexing and ranked retrieval. The corpus used was the ‘Amazon Costumer Reviews Dataset’, more specificaly the file "amazon_reviews_us_Digital_Music_Purchase_v1_00".

## Usage

There are 2 programs to run, the build_index.py script that constructs the index and stores auxiliary dictionaries in files, there is one mandatory argument and 4 optional ones.

`-f or --file`

Argument to pass the name of the file to be indexed, mandatory by the programm.

`-l or --length`

Optional argument that sets a minimum length a word needs to be indexed by the program.

`-sw or --stopwords`

Optional argument that sets a the list of stopwords to be ignored during tokenization by the program. One should pass the name of the file containing the list, a default one is provided, and an empty file is present to use if the user wants to not use any stopwords.

`-st or --stemming`

Optional argument that defines if the stemmer will be used or not by the program. Can be True or False.

`-r or --ranking`

Optional argument that defines the type of ranking to be used by the program. Can only be 'lnc'(signifying the first part of tf-idf ranking settings) or 'bm25'.
Despite the script being ready to implement configurations for the settings of tf-idf ranking, due to lack of time and frustration with errors, the only implemented settings were the mandatory lnc.ltc.


In regards to making a query, one must run the query_index.py script which will prompt a menu and print the top ranked documents according to the built index's parameters.

### Default values

It's important to note that there are default values for each of the optional arguments. These are 4 for the minimum word length, the 'stopwords.txt' file that includes basic english stopwords, True for stemming and 'lnc' for ranking.



## Usage

To run the program with default values:

```bash
python main.py -f 'amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz'
```

To run, for example, the program considering only words with 8 or more length, an empty stopword list, no stemming and the BM25 ranking method:

```bash
python main.py -l 8 -sw 'emptystopwords.txt' -st False -r 'bm25' -f 'amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz'
```

## Results

The results can be found in the folder named as such, there is one file per ranking method that details the top 100 ranked documents in the Digital_Music_Purchase corpus for each of the provided queries and their respective score.

&nbsp;
&nbsp;
&nbsp;
&nbsp;

### Project done by Rui Fernandes, Nmec: 92952