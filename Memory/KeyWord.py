import json
import sqlite3
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT

#相对路径  ../  父文件夹
stopwords_file = './stop/stopwords-master/baidu_stopwords.txt'        #百度停用词表


def load_keybert():
    model = SentenceTransformer('../model/paraphrase-multilingual-MiniLM-L12-v2')  #要下全
    kw_model = KeyBERT(model=model)
    return kw_model

# 全局变量，存储停用词集合
stop_words = set()

def load_stopwords(stopwords_file):
    global stop_words
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        stop_words = {line.strip() for line in f.readlines()}
        

keybert_model=load_keybert()
load_stopwords(stopwords_file)

import jieba

import numpy as np
from collections import defaultdict

BASEMEMO = 2515
NUM_MEMO_PER_INDEX = 5
NUM_ALL = 15


#提取关键词
def extract_keywords(sentence:str):
    try:
        words = ' '.join(jieba.lcut(sentence))
        keywords_list = keybert_model.extract_keywords(words)
        keywords_with_prob = []
        pc = 0 
        for item in keywords_list:
            if item[0] in stop_words:
                continue
            if item[1] > 0.5:
                keywords_with_prob.append({'keyword': item[0], 'kp1': item[1]})
                continue
            if item[1] > 0.4:
                keywords_with_prob.append({'keyword': item[0], 'kp1': item[1]})
                break
            else:
                break
        return keywords_with_prob
    except Exception as e:
        print(e)
        return []
