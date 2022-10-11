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
import numpy
import string
from nltk.stem.snowball import SnowballStemmer
csv.field_size_limit(2147483647)

class Parser:
    def __init__(self, file_name):
        self.file_name = file_name
        if file_name!=None:
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
            content = self.split_line(full_line)
            parsed_content = self.parse_line(content)
            return full_line[2], parsed_content
        except StopIteration:
            return None, None

    def split_line(self, full_line):
        return full_line[5]+" "+full_line[12]+" "+full_line[13]

    def parse_line(self, content):
        allowed_chars = list(string.ascii_lowercase)
        allowed_chars.append(' ')
        #Initial formating of content, removing uppercase, then html tags and finally all non alphabetic symbols or spaces
        temp_txt = content.lower()
        temp_txt = re.sub(r"<[^>]*>", " ", temp_txt)
        temp_txt = ''.join(i for i in temp_txt if i in allowed_chars)

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
    def __init__(self, tokenizer, signature, rank_method='lnc', memory_limit=4000000, posting_limit=None):
        self.tokenizer = tokenizer
        self.signature = signature
        self.memory_limit = memory_limit
        self.posting_limit = posting_limit
        self.rank_method = rank_method
        self.N = 1
        self.id_dict = {}
        self.doc_length = {}
        self.avg_doc_length = 0

    def calculate_frequency(self, term, token_stream):
        if self.rank_method=='lnc':
            return round(1+numpy.log10(token_stream.count(term)),2)
        if self.rank_method=='bm25':
            return token_stream.count(term)
    
    def calculate_positions(self, term, token_stream):
        return [i+1 for i, x in enumerate(token_stream) if x == term]

    def register_doc_length(self, doc_id, term_frequency):
        if self.rank_method=='lnc':
            self.doc_length[doc_id] += term_frequency**2
        if self.rank_method=='bm25':
            self.doc_length[doc_id] += term_frequency


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

        with open('id_dict.txt', "w", encoding='utf-8') as id_file:
            id_file.write(json.dumps(self.id_dict))

        if self.rank_method!='bm25':
            self.doc_length = {key:round(numpy.sqrt(value),2) for (key,value) in self.doc_length.items()}

        with open('doc_length_dict.txt', "w", encoding='utf-8') as len_file:
            len_file.write(json.dumps(self.doc_length))

        self.merge_blocks(block_files)

        return True

    def spimi_invert_mem(self, block_file_name):
        index = {}

        while(sys.getsizeof(index)<self.memory_limit):
            doc_id, token_stream = self.tokenizer.get_token_stream()

            if(doc_id):
                #Record in the id dictionary
                self.id_dict[self.N] = doc_id ; doc_id = self.N ; self.N+=1

                #Initialize doc_length for this doc
                self.doc_length[doc_id]=0

                for term in set(token_stream):
                    term_frequency = self.calculate_frequency(term, token_stream)
                    positions = self.calculate_positions(term, token_stream)
                    self.register_doc_length(doc_id,term_frequency)
                    if term in index:
                        index[term].append((doc_id,term_frequency, positions))
                    else:
                        index[term] = [(doc_id,term_frequency, positions)]
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
                #Record in the id dictionary
                self.id_dict[self.N] = doc_id ; doc_id = self.N ; self.N+=1 

                #Initialize doc_length for this doc
                self.doc_length[doc_id]=0

                for term in token_stream:
                    term_frequency = self.calculate_frequency(term, token_stream)
                    positions = self.calculate_positions(term, token_stream)
                    self.register_doc_length(doc_id,term_frequency)
                    postings_count+=1
                    if term in index:
                        index[term].append((doc_id,term_frequency,positions))
                    else:
                        index[term] = [(doc_id,term_frequency,positions)]
            else:
                return False
            
        sorted_terms = sorted(index.keys())
        self.write_block(sorted_terms, index, block_file_name)

        return True

    def write_block(self, sorted_terms, index, block_file_name):

        with open(block_file_name, 'w', encoding='utf-8') as f:
            for term in sorted_terms:
                line = "%s %s\n" % (term, ''.join([";"+str(doc[0])+":"+str(doc[1])+':'+str(doc[2])[1:-1].replace(" ", "") for doc in index[term]]))
                f.write(line)
        return True

    def merge_blocks(self, block_file_names):

        #Variables for saving alpabhetic ordered index blocks
        all_chars = list(string.ascii_lowercase)
        current_pos = -len(self.signature)
        current_char = 'a'
        char_blocks = {}
        
        
        #open all block files at the same time and read the first line from them
        block_files = [open(block_file, 'r', encoding='utf-8') for block_file in block_file_names]
        lines = [block_file.readline()[:-1] for block_file in block_files]
        most_recent_term = ""

        # remove empty blocks from list
        i = 0
        for b in block_files:
            if lines[i] == "":
                block_files.pop(i)
                lines.pop(i)
            else:
                i += 1

        # fill the final index file
        with open('final_index.txt', "w", encoding='utf-8') as output:
            output.write(self.signature)
            while len(block_files) > 0:

                min_index = lines.index(min(lines))
                line = lines[min_index]
                current_term = line.split()[0]
                current_postings = "".join(map(str, sorted(list(map(str, line.split()[1:])))))

                #Check if new initial character and register in char_blocks dictionary
                if current_term[0] != current_char:
                    char_blocks[current_char]=current_pos
                    current_char = all_chars[all_chars.index(current_char)+1]

                if current_term != most_recent_term:
                    output.write("\n%s%s" % (current_term, current_postings))
                    current_pos+= len(current_term)+len(current_postings)+1
                    most_recent_term = current_term
                else:
                    output.write("%s" % current_postings)
                    current_pos+= len(current_postings)

                lines[min_index] = block_files[min_index].readline()[:-1]

                if lines[min_index] == "":
                    block_files[min_index].close()
                    block_files.pop(min_index)
                    lines.pop(min_index)
            
            
            char_blocks['z']=output.tell()
            output.close()

        #Write alphabetic blocks to file
        with open('index_blocks.txt', "w", encoding='utf-8') as block_f:
            block_f.write(json.dumps(char_blocks))

        #clean all temporary index files
        [os.remove(block_file) for block_file in block_file_names]

        return True

    def generate_idf_dic(self):
        IDF_dict = {}
        with open('final_index.txt', "r", encoding='utf-8') as index:
            line = index.readline()
            while(True):
                line = index.readline()
                if not line:
                    break
                IDF_dict[line.split(';')[0]] = round(numpy.log10((self.N-1)/(len(line.split(';'))-1)) , 2)
        
        with open('IDF_dict.txt', "w", encoding='utf-8') as IDF_dict_f:
            IDF_dict_f.write(json.dumps(IDF_dict))

def main():

    # Defining all arguments
    argparser = argparse.ArgumentParser(description='Index builder')
    argparser.add_argument('-l', '--length', help='Minimum length of words', default=4)
    argparser.add_argument('-sw', '--stopwords', help='File to read for stopwords', default='stopwords.txt')
    argparser.add_argument('-st', '--stemming', help='Use stemming or not', default=True)
    argparser.add_argument('-r', '--ranking', help='Ranking method', default='lnc')
    requiredNamed = argparser.add_argument_group('Required named arguments')
    requiredNamed.add_argument('-f', '--file', help='Input file name', required=True)
    
    args = argparser.parse_args()

    if not os.path.isfile(args.file):
        raise Exception("Given file does not exist")

    index_time = time.time()

    parser = Parser(args.file)
    tokenizer = Tokenizer(parser, int(args.length), args.stopwords, args.stemming)
    signature = f'{args.file} {args.length} {args.stopwords} {args.stemming} {args.ranking}'
    indexer = SPIMI(tokenizer, signature, args.ranking)

    #dummy return result is requested to force the operaion to finish before constructing the DF dictionary
    ret = indexer.build_index()

    print("Total indexing time is: %s" % (time.time() - index_time))

    print("Total index size on disk: "+str(os.path.getsize("final_index.txt")/1024/1024)+"MB")


    indexer.generate_idf_dic()

if __name__== "__main__":
    main()
