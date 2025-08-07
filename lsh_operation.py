
from pyspark.sql import SparkSession
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import RegexTokenizer, NGram, HashingTF, MinHashLSH


def filter_unique_code_blocks(blocks, threshold=0.8):
    spark = SparkSession.builder.appName("CloneFilter").master("local[*]").getOrCreate()
    try:
        added_blocks = blocks['added']
        removed_blocks = blocks['removed']
        
        # Criar DataFrames
        df_added = spark.createDataFrame([(i, code['block'], code['filename']) for i, code in enumerate(added_blocks)], ["id", "code", "filename"])
        df_removed = spark.createDataFrame([(i, code['block'], code['filename']) for i, code in enumerate(removed_blocks)], ["id", "code", "filename"])

        # Pipeline de processamento
        tokenizer = RegexTokenizer(inputCol="code", outputCol="tokens", pattern=r"\W+", toLowercase=True)
        ngram = NGram(n=4, inputCol="tokens", outputCol="ngrams")
        hashingTF = HashingTF(inputCol="ngrams", outputCol="features", numFeatures=1024)
        minhash = MinHashLSH(inputCol="features", outputCol="hashes", numHashTables=10)

        pipeline = Pipeline(stages=[tokenizer, ngram, hashingTF, minhash])
        model = pipeline.fit(df_added.union(df_removed))

        df_added_trans = model.transform(df_added)
        df_removed_trans = model.transform(df_removed)

        # Comparar os métodos
        similar = model.stages[-1].approxSimilarityJoin(df_added_trans, df_removed_trans, threshold, distCol="JaccardDistance")
        matched_ids_added = [row.datasetA.id for row in similar.collect()]
        matched_ids_removed = [row.datasetB.id for row in similar.collect()]

        # Filtrar listas
        set_added = set(matched_ids_added)
        set_removed = set(matched_ids_removed)

        if len(set_added) >= 1 or len(set_removed):
            print('find similar')

        blocks['added'] = [{'block': code['block'], 'filename': code['filename']} for i, code in enumerate(added_blocks) if i not in set_added]
        blocks['removed'] = [{'block': code['block'], 'filename': code['filename']} for i, code in enumerate(removed_blocks) if i not in set_removed]

    except:
         pass

    spark.stop()
    return blocks


# Inicializar sessão Spark (se ainda não estiver inicializada)
spark = SparkSession.builder.getOrCreate()

def remove_code_clones(blocks, similarity_threshold=0.95):
    added_blocks = blocks['added']
    removed_blocks = blocks['removed']

    if not added_blocks or not removed_blocks:
        return blocks  # Nada a comparar

    # Extrair blocos de código
    added_code_blocks = [code['block'] for code in added_blocks]
    removed_code_blocks = [code['block'] for code in removed_blocks]

    # Calcular vetores TF-IDF
    all_blocks = added_code_blocks + removed_code_blocks
    vectorizer = TfidfVectorizer().fit(all_blocks)
    tfidf_matrix = vectorizer.transform(all_blocks)

    # Dividir matriz
    added_matrix = tfidf_matrix[:len(added_code_blocks)]
    removed_matrix = tfidf_matrix[len(added_code_blocks):]

    # Calcular similaridade de coseno
    similarity_matrix = cosine_similarity(added_matrix, removed_matrix)

    # Encontrar pares semelhantes acima do threshold
    similar_pairs = set()
    for i in range(similarity_matrix.shape[0]):
        for j in range(similarity_matrix.shape[1]):
            if similarity_matrix[i, j] >= similarity_threshold:
                similar_pairs.add((i, j))

    # Remover blocos similares
    added_indices_to_remove = set(i for i, _ in similar_pairs)
    removed_indices_to_remove = set(j for _, j in similar_pairs)

    blocks['added'] = [code for i, code in enumerate(added_blocks) if i not in added_indices_to_remove]
    blocks['removed'] = [code for j, code in enumerate(removed_blocks) if j not in removed_indices_to_remove]

    return blocks
