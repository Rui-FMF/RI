# Rui Fernandes
# MEI 2021/2022
# NMEC: 92952

import csv
import os
import json
import numpy
import string
import build_index as builder
csv.field_size_limit(2147483647)


def calc_bm25_score(term, doc, doc_length_dict, avg_doc_length, IDF_dict, k, b):
        idf = IDF_dict[term] if term in IDF_dict else 0

        return idf * ((k+1)*int(doc[1]))/( k*( (1-b) + (b*doc_length_dict[doc[0]]/avg_doc_length)) +int(doc[1]))


def calculate_doc_weight(doc, doc_length_dict, ranking):
        if ranking=='lnc':
            return float(doc[1])/doc_length_dict[doc[0]]



def calculate_query_weight(query, IDF_dict, ranking):

        if ranking=='ltc':
            frequencies = {t:round(1+numpy.log10(query.count(t)),2) for t in set(query)}
            weights = {(k):(v*IDF_dict[k] if k in IDF_dict else 0) for (k,v) in frequencies.items()}
            query_len = numpy.sqrt(sum([f**2 for f in weights.values()]))
            return {k:v/query_len for (k,v) in weights.items()}


def make_query(query, length, stopwords, stemming, ranking, query_ranking, k=1.2, b=0.75):
    
    parser = builder.Parser(None)
    tokenizer = builder.Tokenizer(parser, length, stopwords, stemming)

    parsed_query = parser.parse_line(query)
    tokenized_query = tokenizer.process_tokens(parsed_query)

    with open('index_blocks.txt') as index_blocks_file:
        dic_data = index_blocks_file.read()
    index_blocks_file.close()
    index_blocks_dic = json.loads(dic_data)

    with open('doc_length_dict.txt') as doc_length_file:
        dic_data = doc_length_file.read()
    doc_length_file.close()
    doc_length_dict = json.loads(dic_data)

    with open('IDF_dict.txt') as IDF_file:
            dic_data = IDF_file.read()
    IDF_file.close()
    IDF_dict = json.loads(dic_data)

    N = len(doc_length_dict)
    avg_doc_length = sum(doc_length_dict.values())/N
    all_chars = list(string.ascii_lowercase)

    Scores = dict.fromkeys(range(1,N+1),0)
    if ranking!='bm25':
        query_weights = calculate_query_weight(tokenized_query, IDF_dict, query_ranking)

    for term in tokenized_query:
        char = term[0]
        if char=='z':
            next_char==''
        else:
            next_char = all_chars[all_chars.index(char)+1]
        with open('final_index.txt', "r", encoding='utf-8') as index:
            if char == 'a':
                index.readline()
            else:
                index.seek( index_blocks_dic[all_chars[all_chars.index(char)-1]] )
            
            while True:
                line = index.readline()
                if line[0]==next_char:
                    term_documents=None
                    break

                split_line = line.strip().split(';')
                if split_line[0]==term:
                    term_documents = [(i.split(':')[0],i.split(':')[1]) for i in split_line[1:]]
                    break
        index.close()

        if term_documents==None:
            continue

        for doc in term_documents:
            if ranking=='bm25':
                score = calc_bm25_score(term, doc, doc_length_dict, avg_doc_length, IDF_dict, k, b)
                Scores[int(doc[0])] += score
            else:
                term_weight = calculate_doc_weight(doc, doc_length_dict, ranking)
                Scores[int(doc[0])] += term_weight*query_weights[term]

    top_docs = [(k,v) for k,v in sorted(Scores.items(), key=lambda item: item[1], reverse=True)[0:100]]

    with open('id_dict.txt') as id_file:
        dic_data = id_file.read()
    id_file.close()
    id_dict = json.loads(dic_data)

    return top_docs, id_dict
            

def main():

    if os.path.exists('./final_index.txt'):
        with open('final_index.txt', "r", encoding='utf-8') as index:
            info = index.readline().split()
            original_file = info[0] ; length = info[1] ; stopwords = info[2] ; stemming = info[3] ; ranking = info[4]
        index.close()
        print("Current index built with the file: "+original_file+" with following parameters:")
        print("Minimum word length: "+length)
        print("Stopword file: "+stopwords)
        if ranking=='bm25':
            print("Ranking method: "+ranking)
        else:
            print("Ranking method: tf-idf with "+ranking+" settings")
    else:
        print("No index built...")
        return



    while True:
        print('\n [1] Query \n [2] Exit \n')
        choice = input("Enter your choice: ")
        
        if choice=='1':
            if ranking=='bm25':
                k = input("Chose value for k ")
                b = input("Chose value for b ")
                query = input("Enter a query ")
                top_docs, id_dict = make_query(query, int(length), stopwords, stemming, ranking, 'bm25', float(k), float(b))
            else:
                query = input("Enter a query ")
                top_docs, id_dict = make_query(query, int(length), stopwords, stemming, ranking, 'ltc')

            print("The best ranked documents for "+query+" are as follows: ")
            for d in top_docs:
                print(f'{id_dict[str(d[0])]} with {d[1]} score')

        elif choice=='2':
            break
        else:
            print("Wrong option selection. Try again..")


    

if __name__== "__main__":
    main()
