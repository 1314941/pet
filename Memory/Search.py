"""
This script showcases a recommended approach to perform semantic search using quantized embeddings with FAISS and usearch.
In particular, it uses binary search with int8 rescoring. The binary search is highly efficient, and its index can be kept
in memory even for massive datasets: it takes (num_dimensions * num_documents / 8) bytes, i.e. 1.19GB for 10 million embeddings.

使用FAISS和usearch进行量化嵌入的语义搜索。具体来说，它使用二进制搜索和int8重新打分。二进制搜索非常高效，其索引可以保存在内存中，即使是对于大规模的数据集也是如此。它需要(num_dimensions * num_documents / 8)字节，即对于1000万个嵌入，需要1.19GB。

首先，代码加载了一个模型和一个语料库。然后，它尝试加载预先计算的二进制和int8索引。如果这些索引不存在，它将计算它们并保存到磁盘上。

search函数执行以下步骤：

将查询嵌入为float32格式。
将查询量化为ubinary格式。
使用二进制索引进行搜索。
加载对应的int8嵌入。
使用float32查询嵌入和int8文档嵌入对前top_k * rescore_multiplier个结果进行重新打分。
对分数进行排序并返回前top_k个结果。

"""


import json
import os
import time

import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_transformers.quantization import quantize_embeddings
from datasets import load_dataset
from Load_Memory import get_all_memories
from Character_Model import get_memory_content_by_character
import faiss
from usearch.index import Index
import Prompt
from datetime import datetime
# We use usearch as it can efficiently load int8 vectors from disk.

# Load the model
# NOTE: Because we are only comparing questions here, we will use the "query" prompt for everything.
# Normally you don't use this prompt for documents, but only for the queries
model = SentenceTransformer(
        "../model/paraphrase-multilingual-MiniLM-L12-v2",
        prompts={"query": "Represent this sentence for searching relevant passages: "},
        default_prompt_name="query",
    )


current_time=datetime.now().strftime('%Y-%m-%d')


class Search():
    def __init__(self,character_name=Prompt.character_name):
        self.index_dir='./index'
        #确保存在
        os.makedirs(self.index_dir, exist_ok=True)
        #默认的索引文件名
        self.usearch_int8_file=self.index_dir+f'/{character_name}_usearch_int8_{current_time}.index'
        self.faiss_ubinary_file=self.index_dir+f'/{character_name}_quora_faiss_ubinary{current_time}.index'

        # Apply some default query
        query = "How do I become a good programmer?"

        self.int8_view=None
        # Load the dataset
        self.corpus=None

        self.binary_index=None
        self.int8_view=None
        self.character_name=character_name
        self.init_sqlite3()
        # self.init_neo4j(character_name)

    def init_sqlite3(self):
        # Load the dataset
        
        self.corpus,self.sqlites_ids=get_all_memories()
        print("corpus length:",len(self.corpus))
        print("sqlites_ids length:",len(self.sqlites_ids))
        self.load_index()


    def init_neo4j(self):
        self.corpus=get_memory_content_by_character(self.character_name)
        self.usearch_int8_file=f'{self.character_name}_usearch_int8.index'
        self.faiss_ubinary_file=f'{self.character_name}_faiss_ubinary.index'
        self.load_index()


    def load_index(self):  
        # Try to load the precomputed binary and int8 indices
        if os.path.exists(self.faiss_ubinary_file):
            self.binary_index: faiss.IndexBinaryFlat = faiss.read_index_binary(self.faiss_ubinary_file)
            self.int8_view = Index.restore(self.usearch_int8_file, view=True)

        else:
            # Encode the corpus using the full precision
            full_corpus_embeddings = model.encode(self.corpus, normalize_embeddings=True, show_progress_bar=True)
                # 获取嵌入向量的维度
            # 检查嵌入向量的维度
            print("嵌入向量的维度:", full_corpus_embeddings.shape)
            embedding_dim = full_corpus_embeddings.shape[1]


            # Convert the embeddings to "ubinary" for efficient FAISS search
            ubinary_embeddings = quantize_embeddings(full_corpus_embeddings, "ubinary")
            self.binary_index = faiss.IndexBinaryFlat(embedding_dim)
            self.binary_index.add(ubinary_embeddings)
            faiss.write_index_binary(self.binary_index, self.faiss_ubinary_file)

            # Convert the embeddings to "int8" for efficiently loading int8 indices with usearch
            int8_embeddings = quantize_embeddings(full_corpus_embeddings, "int8")
            index = Index(ndim=embedding_dim, metric="ip", dtype="i8")
            index.add(np.arange(len(int8_embeddings)), int8_embeddings)
            index.save(self.usearch_int8_file)
            del index

            # Load the int8 index as a view, which does not cost any memory
            self.int8_view = Index.restore(self.usearch_int8_file, view=True)


        if self.int8_view is None:
            raise ValueError("Failed to load the int8 index")

    def search(self,query, top_k: int = 10, rescore_multiplier: int = 4):    #数据库发生变化时，最好重新加载索引  推荐 两个数据库  一个存档  一个记录  定时更新
        try:
            # 1. Embed the query as float32
            start_time = time.time()
            query_embedding = model.encode(query)
            embed_time = time.time() - start_time

            # 2. Quantize the query to ubinary
            start_time = time.time()
            query_embedding_ubinary = quantize_embeddings(query_embedding.reshape(1, -1), "ubinary")
            quantize_time = time.time() - start_time

            # 3. Search the binary index
            start_time = time.time()
            _scores, binary_ids = self.binary_index.search(query_embedding_ubinary, top_k * rescore_multiplier)
            binary_ids = binary_ids[0]
            search_time = time.time() - start_time

            # 4. Load the corresponding int8 embeddings
            start_time = time.time()
            int8_embeddings = self.int8_view[binary_ids].astype(int)
            load_time = time.time() - start_time

            # 5. Rescore the top_k * rescore_multiplier using the float32 query embedding and the int8 document embeddings
            start_time = time.time()
            scores = query_embedding @ int8_embeddings.T
            rescore_time = time.time() - start_time

            # 6. Sort the scores and return the top_k
            start_time = time.time()
            indices = (-scores).argsort()[:top_k]
            top_k_indices = binary_ids[indices]
            top_k_scores = scores[indices]
            sort_time = time.time() - start_time

            return (
                top_k_scores.tolist(),
                top_k_indices.tolist(),
                {
                    "Embed Time": f"{embed_time:.4f} s",
                    "Quantize Time": f"{quantize_time:.4f} s",
                    "Search Time": f"{search_time:.4f} s",
                    "Load Time": f"{load_time:.4f} s",
                    "Rescore Time": f"{rescore_time:.4f} s",
                    "Sort Time": f"{sort_time:.4f} s",
                    "Total Retrieval Time": f"{quantize_time + search_time + load_time + rescore_time + sort_time:.4f} s",
                },
            )
        except Exception as e:
            print("search error:",e)
            return [],[],{}


    def retrieve_and_rank(self,query,top_k=3,rescore_multiplier=4):
        try:
            scores, indices, timings = self.search(query,top_k=top_k,rescore_multiplier=rescore_multiplier)

            # Output the results
            print(f"Timings:\n{json.dumps(timings, indent=2)}")
            print(f"Query: {query}")
            id=[]
            for score, index in zip(scores, indices):
                print("index:",index)
                print(f"(Score: {score:.4f}) {self.corpus[index]}")
                id.append(self.sqlites_ids[index])
            print("")
            return id
        except Exception as e:
            print("retrieve_and_rank error:",e)
            id=[]

            return id

        # 10. Prompt for more queries
        #query = input("Please enter a question: ")




#短期记忆 搜索  轻量化
class Search_history():
    def __init__(self,content:list[str]):
        self.corpus=content
        timestamp=datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dir='./index'
        os.makedirs(dir, exist_ok=True)
        dir='./index/temp'
        os.makedirs(dir, exist_ok=True)
        self.usearch_int8_file=f'index/temp/{timestamp}_usearch_int8.index'
        self.faiss_ubinary_file=f'index/temp/{timestamp}_faiss_ubinary.index'
        self.load_index()


    def load_index(self):  
        # Encode the corpus using the full precision
        full_corpus_embeddings = model.encode(self.corpus, normalize_embeddings=True, show_progress_bar=True)
            # 获取嵌入向量的维度
        # 检查嵌入向量的维度
        print("嵌入向量的维度:", full_corpus_embeddings.shape)
        embedding_dim = full_corpus_embeddings.shape[1]


        # Convert the embeddings to "ubinary" for efficient FAISS search
        ubinary_embeddings = quantize_embeddings(full_corpus_embeddings, "ubinary")
        self.binary_index = faiss.IndexBinaryFlat(embedding_dim)
        self.binary_index.add(ubinary_embeddings)
        faiss.write_index_binary(self.binary_index, self.faiss_ubinary_file)

        # Convert the embeddings to "int8" for efficiently loading int8 indices with usearch
        int8_embeddings = quantize_embeddings(full_corpus_embeddings, "int8")
        index = Index(ndim=embedding_dim, metric="ip", dtype="i8")
        index.add(np.arange(len(int8_embeddings)), int8_embeddings)
        index.save(self.usearch_int8_file)
        del index

        # Load the int8 index as a view, which does not cost any memory
        self.int8_view = Index.restore(self.usearch_int8_file, view=True)


        if self.int8_view is None:
            raise ValueError("Failed to load the int8 index")

    def search(self,query, top_k: int = 10, rescore_multiplier: int = 4):    #数据库发生变化时，最好重新加载索引  推荐 两个数据库  一个存档  一个记录  定时更新
        try:
            # 1. Embed the query as float32
            start_time = time.time()
            query_embedding = model.encode(query)
            embed_time = time.time() - start_time

            # 2. Quantize the query to ubinary
            start_time = time.time()
            query_embedding_ubinary = quantize_embeddings(query_embedding.reshape(1, -1), "ubinary")
            quantize_time = time.time() - start_time

            # 3. Search the binary index
            start_time = time.time()
            _scores, binary_ids = self.binary_index.search(query_embedding_ubinary, top_k * rescore_multiplier)
            binary_ids = binary_ids[0]
            search_time = time.time() - start_time

            # 4. Load the corresponding int8 embeddings
            start_time = time.time()
            int8_embeddings = self.int8_view[binary_ids].astype(int)
            load_time = time.time() - start_time

            # 5. Rescore the top_k * rescore_multiplier using the float32 query embedding and the int8 document embeddings
            start_time = time.time()
            scores = query_embedding @ int8_embeddings.T
            rescore_time = time.time() - start_time

            # 6. Sort the scores and return the top_k
            start_time = time.time()
            indices = (-scores).argsort()[:top_k]
            top_k_indices = binary_ids[indices]
            top_k_scores = scores[indices]
            sort_time = time.time() - start_time

            return (
                top_k_scores.tolist(),
                top_k_indices.tolist(),
                {
                    "Embed Time": f"{embed_time:.4f} s",
                    "Quantize Time": f"{quantize_time:.4f} s",
                    "Search Time": f"{search_time:.4f} s",
                    "Load Time": f"{load_time:.4f} s",
                    "Rescore Time": f"{rescore_time:.4f} s",
                    "Sort Time": f"{sort_time:.4f} s",
                    "Total Retrieval Time": f"{quantize_time + search_time + load_time + rescore_time + sort_time:.4f} s",
                },
            )
        except Exception as e:
            print("search error:",e)
            return [],[],{}


    def retrieve_and_rank(self,query,top_k=3,rescore_multiplier=4):
        try:
            scores, indices, timings = self.search(query,top_k=top_k,rescore_multiplier=rescore_multiplier)

            # Output the results
            print(f"Timings:\n{json.dumps(timings, indent=2)}")
            print(f"Query: {query}")
            id=[]
            for score, index in zip(scores, indices):
                print("index:",index)
                print(f"(Score: {score:.4f}) {self.corpus[index]}")
                id.append(index)
            print("")
            return id
        except Exception as e:
            print("retrieve_and_rank error:",e)
            id=[]

            return id



