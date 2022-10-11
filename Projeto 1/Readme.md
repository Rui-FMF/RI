# RI - Assignment 1

This assignment consisted in making a simple document indexer using the SPIMI approach. The corpus used was the ‘Amazon Costumer Reviews Dataset’, 4 of the files being tested.

## Usage

The program to run is simply called main.py, there is one mandatory argument and 3 optional ones.

`-f or --file`

Argument to pass the name of the file to be indexed, mandatory by the programm.

`-l or --length`

Optional argument that sets a minimum length a word needs to be indexed by the program.

`-sw or --stopwords`

Optional argument that sets a the list of stopwords to be ignored during tokenization by the program. One should pass the name of the file containing the list, a default one is provided, and an empty file is present to use if the user wants to not use any stopwords.

`-st or --stemming`

Optional argument that defines if the stemmer will be used or not by the program. Can be True or False.

### Default values

It's important to note that there are default values for each of the optional arguments. These are 4 for the minimum word length, the 'stopwords.txt' file that includes basic english stopwords, and True for stemming.



## Usage

To run the program with default values:

```bash
python main.py -f 'amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz'
```

To run, for example, the program considering only words with 8 or more length, an empty stopword list and no stemming:

```bash
python main.py -l 8 -sw 'emptystopwords.txt' -st False -f 'amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz'
```

## Results

The following table details the requested result values for the 4 files to index, noting that they all were indexed considering a temporary index memory limit of 800 thousand bytes, and with the largest 2 files and extra run was made considering instead 15 Milion bytes of memory.


|        File        | Total indexing time | Index size on disk | Vocabulary size | Nº of temporary indexes | Time to start index searching |
|:------------------:|:-------------------:|:------------------:|:---------------:|:-----------------------:|:-----------------------------:|
|     Video Games    |         16s         |        72 MB       |      74096      |            7            |             0.68s             |
|    Digital Music   |         156s        |       584 MB       |      505606     |           124           |             6.61s             |
| Music (800k bytes) |        1682s        |       3884 MB      |     2547011     |           1138          |             44.21s            |
|  Music (15M bytes) |         934s        |       3884 MB      |     2547011     |            16           |             45.80s            |
| Books (800k bytes) |        3009s        |       6985 MB      |     2573061     |           1535          |             87.09             |
|  Books (15M bytes) |        1641s        |       6985 MB      |     2573061     |            18           |             87.05             |


&nbsp;
&nbsp;
&nbsp;
&nbsp;

### Project done by Rui Fernandes, Nmec: 92952