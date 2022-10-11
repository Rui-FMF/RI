from audioop import avg
from glob import escape
from math import log2
import time
import query_index as make_query

def calc_measures(relevant, retrieved_docs, id_dict):
    relevant_docs = relevant.keys()
    tp = 0
    ideal_scores = [int(s) for s in relevant.values()]
    real_scores = []

    for retrieved in retrieved_docs:
        r_doc = id_dict[str(retrieved[0])]
        if r_doc in relevant_docs:
            tp+=1
            real_scores.append(int(relevant[r_doc]))
        else:
            real_scores.append(0)
    
    precision = tp/len(retrieved_docs)
    recall = tp/len(relevant_docs)
    if precision+recall==0:
        f_score = 0
    else:
        f_score = 2*precision*recall/(precision+recall)

    real_DCG = [real_scores[0]] + [real_scores[i]/log2(i+1) for i in range(1,len(real_scores))]
    ideal_DCG = [ideal_scores[0]] + [ideal_scores[i]/log2(i+1) for i in range(1,len(real_scores))]
    NDCG = sum([real_DCG[i]/ideal_DCG[i] for i in range(0,len(real_scores))])

    return precision, recall, f_score, NDCG


with open('queries.txt', "r", encoding='utf-8') as query_file:
    queries = query_file.readlines()
    queries = [line.strip() for line in queries]
query_file.close()

with open('queries_relevance.txt', "r", encoding='utf-8') as relevant_file:
    queries_relevant_docs = {}
    curent_query = ''
    while(True):
        line = relevant_file.readline()
        if not line:
            break
        if line[0]=='Q':
            curent_query = line.split(':')[1].strip()
            queries_relevant_docs[curent_query] = {}
        if line[0]=='R':
            queries_relevant_docs[curent_query][line.split()[0]] = line.split()[1]
relevant_file.close()

times = []
precisions = []

with open('bm25_results.txt', "w", encoding='utf-8') as result_file:
    with open('bm25_stats.txt', "w", encoding='utf-8') as stats_file:
        for l in queries:
            stats_file.write("Stats for query \""+l+"\" are as follows: \n\n")

            start_time = time.time()
            top_docs, id_dict = make_query.make_query(l, 4, 'stopwords.txt', True, 'bm25', 'bm25')
            query_time = time.time() - start_time
            times.append(query_time)

            result_file.write("The best ranked documents for \""+l+"\" are as follows: \n")
            for d in top_docs:
                result_file.write(f'{id_dict[str(d[0])]} with {d[1]} score\n')
            result_file.write('\n\n')

            
            for n in [10,20,50]:
                precision, recall, f_score, NDCG = calc_measures(queries_relevant_docs[l],top_docs[0:n], id_dict)
                precisions.append(precision)
   
                stats_file.write("For top "+str(n)+": \n\n")
                stats_file.write("Precision -> "+str(precision)+"\n")
                stats_file.write("Recall -> "+str(recall)+"\n")
                stats_file.write("F-score -> "+str(f_score)+"\n")
                stats_file.write("NDCG -> "+str(NDCG)+"\n\n")

        stats_file.write("Average stats: \n\n")
        stats_file.write("Query throughput -> "+str(sum(times)/len(times))+"\n")
        stats_file.write("Precision -> "+str(sum(precisions)/len(precisions))+"\n\n\n")

