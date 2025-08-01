from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import RegexTokenizer, NGram, HashingTF, MinHashLSH


def filter_unique_code_blocks(blocks, threshold=0.8):
    spark = SparkSession.builder.appName("CloneFilter").master("local[*]").getOrCreate()
    try:
        added_blocks = blocks['added']
        removed_blocks = blocks['removed']
        
        # Criar DataFrames
        df_added = spark.createDataFrame([(i, code) for i, code in enumerate(added_blocks)], ["id", "code"])
        df_removed = spark.createDataFrame([(i, code) for i, code in enumerate(removed_blocks)], ["id", "code"])

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

        blocks['added'] = [code for i, code in enumerate(added_blocks) if i not in set_added]
        blocks['removed'] = [code for i, code in enumerate(removed_blocks) if i not in set_removed]

    except:
         pass

    spark.stop()
    return blocks