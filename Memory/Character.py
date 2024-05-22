from Character_Model import create_charater,create_memory,review_memory,Memory,Character,find_memory,find_memory_by_character,MemoryNode,get_memory_content_by_character,clean_all_data
import sqlite3
import os
from Search import retrieve_and_rank,init_neo4j
from Load_Memory import find_memory_by_id
import Prompt



#大脑
class Brain():
    def __init__(self,name='xiaobai', age='18', gender='male', species='human', ability='sleep', work='assistant'):
        self.character = Character(name, age, gender, species, ability, work)
        self.characterNode=create_charater(self.character)
    def add_memory(self, memory):
        create_memory(self.characterNode, memory)


    def review_memory(self, memory):
        memory_id = find_memory(self.character, memory.content)
        review_memory(memory_id)

    #在这步之前需要先清洗数据  去掉重复的  空的  方便构建关系
    def load_memory(self,db_file,db_name):  
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {db_name}")
            memories =  cursor.fetchall()
            #输出全部数量，前十个句子
            print(f"共有{len(memories)}条记忆")
            #for i in range(10):
            #    print(memories[i])
            cursor.close()
            conn.close()
            for memory in memories:
                self.add_memory(Memory(memory[1],memory[3],memory[4],memory[5],memory[6],memory[7]))
                #print(memory)
        except Exception as e:
            print("Load memory failed:",e)

    #将记忆进行理解，串联
    def understand_memory(self):
        clean_all_data()  #清洗数据
        memorynodes=get_memory_content_by_character(self.character.name)
        init_neo4j(self.character.name)
        for memorynode in memorynodes:
            ids=retrieve_and_rank(memorynode.content)
            for id in ids:
                memory=find_memory(self.character.name,memorynode[id].content)
                if memory:
                    memorynode.related.connect(memory)

        
            


# 连接到SQLite数据库
db_file=f'../database/charater/{Prompt.character_name}.db'
db_dir='../database'
os.makedirs(db_dir, exist_ok=True)
db_dir='../database/charater'
os.makedirs(db_dir, exist_ok=True)


brain=Brain()
update=input("是否需要更新数据？(y/n):")
if update=='y':
    brain.load_memory(db_file,"xiaobai")
understand=input("是否需要理解记忆？(y/n):")
if understand=='y':
    brain.understand_memory()
