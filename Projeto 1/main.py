# Rui Fernandes
# MEI 2021/2022
# NMEC: 92952

import csv
import sys
import os
import gzip
import re
import time
import json
import argparse
from nltk.stem.snowball import SnowballStemmer
csv.field_size_limit(2147483647)

class Parser:
    def __init__(self, file_name):
        self.file_name = file_name
        self.ziped_file = gzip.open(file_name, 'rt', encoding="utf-8")
        self.tsv_reader = csv.reader(self.ziped_file, delimiter="\t")
        self.line_len = len(next(self.tsv_reader))

    def get_next_line(self):
        #returns id followed by all the parsed content
        l = 0
        try:
            #this while serves to root out missformated lines that don't have the correct number of elements
            while l!=self.line_len:
                full_line = next(self.tsv_reader)
                l = len(full_line)
            parsed_content = self.parse_line(full_line)
            return full_line[2], parsed_content
        except StopIteration:
            return None, None

    def parse_line(self, full_line):
        #Initial formating of content, removing uppercase, then html tags and finally all non alphabetic symbols or spaces
        temp_txt = full_line[5]+" "+full_line[12]+" "+full_line[13]
        temp_txt = temp_txt.lower()
        temp_txt = re.sub(r"<[^>]*>", " ", temp_txt)
        temp_txt = ''.join(i for i in temp_txt if i.isalpha() or i.isspace())

        tokens = temp_txt.split()
        return tokens


class Tokenizer:
    def __init__(self, parser, min_len=4, stopwords_file='stopwords.txt', use_stemmer=True):
        self.parser = parser
        self.min_len = min_len
        self.stopwords = set([line.rstrip() for line in open(stopwords_file,'r').readlines()])
        self.use_stemmer = use_stemmer
        self.stem_dict = {}
    
    def process_tokens(self, tokens):
        #remove words shorter than given limit or in stopword list
        tokens = [i for i in tokens if len(i)>=self.min_len and i not in self.stopwords]

        #Steming tokens, terms that have been stemed get stored in a dictionary to be acessed later, cutting down time of processing
        if self.use_stemmer==True:
            snow_stemmer = SnowballStemmer(language='english')
            stemmed_tokens = []
            for t in tokens:
                if t in self.stem_dict:
                    stemmed_tokens.append(self.stem_dict.get(t))
                else:
                    stemmed_token = snow_stemmer.stem(t)
                    stemmed_tokens.append(stemmed_token)
                    self.stem_dict[t] = stemmed_token
            return stemmed_tokens

        return tokens

    def get_token_stream(self):
        id, tokens = self.parser.get_next_line()
        if(id):
            return id, self.process_tokens(tokens)
        else:
            return None, None

class SPIMI:
    def __init__(self, tokenizer, memory_limit=800000, posting_limit=None):
        self.tokenizer = tokenizer
        self.memory_limit = memory_limit
        self.posting_limit = posting_limit

    def build_index(self):

        temp_idx_num = 1
        cont = True
        block_files = []
        while(cont):
            block_file_name = './temp_idx_'+str(temp_idx_num)+'.txt'
            block_files.append(block_file_name)
            if(self.memory_limit):
                cont = self.spimi_invert_mem(block_file_name)
            else:
                cont = self.spimi_invert_postings(block_file_name)
            temp_idx_num+=1
        print("Number of temporary index files: "+str(temp_idx_num-1))
        self.merge_blocks(block_files)

        return True

    def spimi_invert_mem(self, block_file_name):
        index = {}

        while(sys.getsizeof(index)<self.memory_limit):
            doc_id, token_stream = self.tokenizer.get_token_stream()

            if(doc_id):
                for term in token_stream:
                    if term in index:
                        index[term].append(doc_id)
                    else:
                        index[term] = [doc_id]
            else:
                sorted_terms = sorted(index.keys())
                self.write_block(sorted_terms, index, block_file_name)
                return False
            
        sorted_terms = sorted(index.keys())
        self.write_block(sorted_terms, index, block_file_name)

        return True

    def spimi_invert_postings(self, block_file_name):
        index = {}
        postings_count = 0

        while(postings_count<self.posting_limit):
            doc_id, token_stream = self.tokenizer.get_token_stream()

            if(doc_id):
                for term in token_stream:
                    postings_count+=1
                    if term in index:
                        index[term].append(doc_id)
                    else:
                        index[term] = [doc_id]
            else:
                return False
            
        sorted_terms = sorted(index.keys())
        self.write_block(sorted_terms, index, block_file_name)

        return True

    def write_block(self, sorted_terms, index, block_file_name):

        with open(block_file_name, 'w', encoding='utf-8') as f:
            for term in sorted_terms:
                line = "%s %s\n" % (term, ' '.join([str(doc_id) for doc_id in index[term]]))
                f.write(line)
        return True

    def merge_blocks(self, block_file_names):
        
        #open all block files at the same time and read the first line from them
        block_files = [open(block_file, 'r', encoding='utf-8') for block_file in block_file_names]
        lines = [block_file.readline()[:-1] for block_file in block_files]
        most_recent_term = ""

        #remove empty blocks from list
        i = 0
        for b in block_files:
            if lines[i] == "":
                block_files.pop(i)
                lines.pop(i)
            else:
                i += 1

        #fill the final index file
        with open('final_index.txt', "w", encoding='utf-8') as output:
            while len(block_files) > 0:

                min_index = lines.index(min(lines))
                line = lines[min_index]
                current_term = line.split()[0]
                current_postings = " ".join(map(str, sorted(list(map(str, line.split()[1:])))))

                if current_term != most_recent_term:
                    output.write("\n%s %s" % (current_term, current_postings))
                    most_recent_term = current_term
                else:
                    output.write(" %s" % current_postings)

                lines[min_index] = block_files[min_index].readline()[:-1]

                if lines[min_index] == "":
                    block_files[min_index].close()
                    block_files.pop(min_index)
                    lines.pop(min_index)

            output.close()

        #clean all temporary index files
        [os.remove(block_file) for block_file in block_file_names]

        return True

def main():

    # Defining all arguments
    argparser = argparse.ArgumentParser(description='Index builder')
    argparser.add_argument('-l', '--length', help='Minimum length of words', default=4)
    argparser.add_argument('-sw', '--stopwords', help='File to read for stopwords', default='stopwords.txt')
    argparser.add_argument('-st', '--stemming', help='Use stemming or not', default=True)
    requiredNamed = argparser.add_argument_group('Required named arguments')
    requiredNamed.add_argument('-f', '--file', help='Input file name', required=True)
    
    args = argparser.parse_args()

    if not os.path.isfile(args.file):
        raise Exception("Given file does not exist")

    index_time = time.time()

    parser = Parser(args.file)
    tokenizer = Tokenizer(parser, int(args.length), args.stopwords, args.stemming)
    indexer = SPIMI(tokenizer)

    #dummy return result is requested to force the operaion to finish before constructing the DF dictionary
    ret = indexer.build_index()

    print("Total indexing time is: %s" % (time.time() - index_time))

    print("Total index size on disk: "+str(os.path.getsize("final_index.txt")/1024/1024)+"MB")
    
    dict_time = time.time()
    DF_dict = {}
    with open('final_index.txt', "r", encoding='utf-8') as index:
        line = index.readline()
        while(True):
            line = index.readline()
            if not line:
                break

            DF_dict[line.split()[0]] = len(line.split())-1
    
    with open('DF_dict.txt', "w", encoding='utf-8') as DF_dict_f:
        DF_dict_f.write(json.dumps(DF_dict))

    print("Time to start up index searcher: %s" % (time.time() - dict_time))

    print("Vocabulary size: "+str(len(DF_dict)))
      
    # Simple Query menu that searches using the dictionary
    snow_stemmer = SnowballStemmer(language='english')
    while True:
        print('\n [1] Query \n [2] Exit \n')
        choice = input("Enter your choice: ")
        
        if choice=='1':     
            query = input("Enter a term to query ")
            stemmed_query = snow_stemmer.stem(query)
            if stemmed_query in DF_dict:
                print("The term "+query+" appears in "+str(DF_dict[stemmed_query])+" documents")
            else:
                print("The term does not appear in any document (might also be a stopword or lower than lenght limit)")
        elif choice=='2':
            break
        else:
            print("Wrong option selection. Try again..")

if __name__== "__main__":
    main()
