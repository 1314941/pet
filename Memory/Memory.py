from neo4j import GraphDatabase
from annoy import AnnoyIndex
from datetime import datetime, timedelta
import random
import torch
from LmStudio import AIMessage,HumanMessage,Message
from transformers import BertTokenizer,BertModel
from Load_Memory import find_memory_by_keywords,MemoryNode,create_charater_memory,detect_character,add_memory,find_memory_by_id,review_memory
from Prompt import prompt_path,prompt_text,default_prompt,character_name
from Search import Search
from decorator import log_task


# 加载bert的分词器
tokenizer = BertTokenizer.from_pretrained('../model/bert-base-chinese')
# 加载bert模型，这个路径文件夹下有bert_config.json配置文件和model.bin模型权重文件
model = BertModel.from_pretrained('../model/bert-base-chinese')


# 初始化向量索引
f = 15  # BERT嵌入向量的维度
t = AnnoyIndex(f, 'dot')  

class Memory():
    def __init__(self,search_obj:Search,target_name=character_name):
        self.character_name = target_name
        self.search_obj=search_obj
        self.load_pet()

    def load_pet(self):
        detect_character(self.character_name)


    @log_task
    def add_memory(self,message:Message,keywords=None):
        # 保存到数据库
        meta_data = {
            "content": message.content,
            "keywords": keywords,
            "importance": 0.5,
            "role": message.role,
            "recall_count": 1,
            "created_time": message.time,
            "updated_time": message.time
        }
        add_memory(meta_data)

          
    #获取记忆
    def load_memory_by_keyword(self,keywords):
        memorynodes=[]
        for keyword in keywords:
            memorynodes.extend(find_memory_by_keywords(keyword))   #根据关键词过滤部分，防止爆显存
        return memorynodes

    # 计算向量表示并构建索引
    def build_index(self, keywords):
        self.memorynodes = self.load_memory_by_keyword(keywords)
        self.memories = [memorynode.content for memorynode in self.memorynodes]
        for i, text in enumerate(self.memories):
            input_ids = tokenizer(text, return_tensors='pt')['input_ids']
            with torch.no_grad():
                embedding = model(input_ids)[0][0].numpy()
            try:
                t.add_item(i, embedding)
            except Exception as e:
                print(f"Error adding item to index: {e}")
        t.build(10)  # 构建树，树的数量可以根据实际情况调整

    # 记忆检索
    def retrieve_memory(self, keywords, inputs):
        try:
            print("记忆检索：",inputs)
            self._nearest_memory_nodes = []
            ids=self.search_obj.retrieve_and_rank(inputs)
            if ids==[] or ids==None:
                return None
            for id in ids:
                print("id:",id)
                node= find_memory_by_id(id)
                if node!=None:
                   print("检索到记忆\n")
                   self._nearest_memory_nodes.append(node)
            #self._nearest_memory_nodes = sorted(self._nearest_memory_nodes, key=lambda x: x.importance, reverse=True)  # 根据权重排序
            # 转换为json格式
            if self._nearest_memory_nodes:
                print("转换记忆格式")
                memories_formatted = self.format_memory(self._nearest_memory_nodes)
                return memories_formatted
            return None
        except Exception as e:
            print(f"Error retrieving memories: {e}")
            return None


    # 计算遗忘程度
    def calculate_forgetting(self,memory):
        # 简化的遗忘曲线算法
        time_since_last_review = datetime.now() - memory.last_review_time
        forgetting_factor = time_since_last_review / timedelta(days=1)  # 假设遗忘速度每天线性增加
        return max(0, memory.weight - forgetting_factor)

    # 模拟复习过程
    def review_memory(self,memories):
        for memory in memories:
            forgetting_degree = self.calculate_forgetting(memory)
            if forgetting_degree > 0.5:  # 假设遗忘程度超过0.5就需要复习
                self.update_weight(memory, memory.weight + 0.1)  # 复习后增加权重
                print(f"Reviewing memory: {memory.content}")

    #转换格式
    def format_memory(self,memorynodes):
        try:
            result=[]
            #后续要添加上用户与宠物标志
            for i, memory in enumerate(memorynodes):
                if memory.role=="assistant":
                    print("添加助理记忆")
                    id=memory.id-1
                    review_memory(id)
                    review_memory(memory.id)
                    node=find_memory_by_id(id)
                    if node!=None:
                        result.append(HumanMessage(node.content))
                    result.append(AIMessage(memory.content))
                else:
                    print("添加主人记忆")
                    result.append(HumanMessage(memory.content))
                    id=memory.id+1
                    review_memory(id)
                    review_memory(memory.id)
                    node=find_memory_by_id(id)
                    if node!=None:
                        result.append(AIMessage(node.content))
            return result
        except Exception as e:
            print("format_memory error:",e)
            return None


'''
while True:
    input_str=input(">")
    memory.add_memory(pet_name, "test", input_str)
    memories=memory.retrieve_memory(input_str)
    memory.review_memory(memories)
    print(memories)
    #转换格式
    memories_formatted=memory.format_memory(memories)
    reponse=model.send_message(memories_formatted)
    output_str=reponse["content"]
    print(output_str)
    memory.add_memory(pet_name, "test", output_str)
'''

