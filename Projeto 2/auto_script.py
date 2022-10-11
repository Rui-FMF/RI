import query_index as make_query

with open('queries.txt', "r", encoding='utf-8') as query_file:
    lines = query_file.readlines()
    lines = [line.strip() for line in lines]
query_file.close()

with open('tf_idf_results.txt', "w", encoding='utf-8') as result_file:
    for l in lines:
        top_docs, id_dict = make_query.make_query(l, 4, 'stopwords.txt', True, 'lnc', 'ltc')
        result_file.write("The best ranked documents for \""+l+"\" are as follows: \n")
        for d in top_docs:
            result_file.write(f'{id_dict[str(d[0])]} with {d[1]} score\n')
        result_file.write('\n\n')
