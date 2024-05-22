import json
import os
from datetime import datetime
import KeyWord 
import sqlite3
import json
from datetime import datetime
#from Prompt import prompt_path,prompt_text,default_prompt,character_name
import Prompt
input_folder='./in'
output_folder = './output'
os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)
meta_file = input_folder + '/train.jsonl'
target_file = input_folder + '/target.json'
import re


# 假设 KeyWord.extract_keywords 是一个已经定义的函数，用于提取关键词
# create_time 应该是一个 datetime 对象，表示创建时间

# 连接到SQLite数据库
db_file=f'../database/charater/{Prompt.character_name}.db'
#存档数据库
archive_db_file=f'../database/charater/{Prompt.character_name}_archive.db'
#创建数据库目录
db_dir='../database'
os.makedirs(db_dir, exist_ok=True)
db_dir='../database/charater'
os.makedirs(db_dir, exist_ok=True)


# 假设这是Neo4j中记忆节点的结构
class MemoryNode:
    def __init__(self,id,content, keyword,role='user', importance=0.5,memory_recall_count=1,created_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),last_review_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        self.id=id
        self.keyword = keyword
        self.content = content
        self.importance = importance
        self.memory_recall_count = memory_recall_count
        self.created_time = created_time
        self.role = role
        self.last_review_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



def init_db():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # 创建表格（如果尚不存在）
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {Prompt.character_name} (
        id INTEGER PRIMARY KEY,
        memory_content TEXT NOT NULL,
        memory_keywords JSON,
        role TEXT,
        importance REAL,
        memory_recall_count INTEGER,
        created_time DATETIME,
        updated_time DATETIME
    )
    ''')
    conn.commit()
    cursor.close()
    conn.close()


def detect_archive_db():
    #如果没有，则创建存档数据库  复制
    if not os.path.exists(archive_db_file):
        #复制数据库
        import shutil
        shutil.copy(db_file, archive_db_file)
        print(f"创建存档数据库{archive_db_file}")



# 添加数据
def add_memory(meta_data):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO {Prompt.character_name} (memory_content, memory_keywords, role, importance, memory_recall_count, created_time, updated_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (meta_data["content"], json.dumps(meta_data["keywords"]), meta_data["role"], meta_data["importance"], meta_data["recall_count"], meta_data["created_time"], meta_data["updated_time"]))
    conn.commit()
    cursor.close()
    conn.close()

# 删除数据
def delete_memory(memory_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute(f"DELETE FROM {Prompt.character_name} WHERE id = ?", (memory_id,))
    conn.commit()
    cursor.close()
    conn.close()

# 查找数据
def find_memory_by_id(memory_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {Prompt.character_name} WHERE id = ?", (memory_id,))
    result = cursor.fetchone()
    #转换为node
    memory=None
    if result:
        memory = MemoryNode(result[0], result[1], json.loads(result[2]), result[3], result[4], result[5], result[6], result[7])
    cursor.close()
    conn.close()
    return memory
 


#获取全部记忆
def get_all_memories():
    detect_archive_db()
    conn = sqlite3.connect(archive_db_file)
    cursor = conn.cursor()
    cursor.execute(f"SELECT memory_content,id FROM {Prompt.character_name}")
    rows=cursor.fetchall()
    memories=[]
    ids=[]
    for row in rows:
        memories.append(row[0])
        ids.append(row[1])
    #输出全部数量，前十个句子
    print(f"共有{len(memories)}条记忆")
    #for i in range(10):
    #    print(memories[i])
    cursor.close()
    conn.close()
    return memories,ids

def keywords_format(keywords:json):
    keywords_list=[]
    for i in range(len(keywords)):
        keywords_list.append(keywords[i])
    return keywords_list


#获取全部关键词
def get_all_keywords():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT keywords FROM {Prompt.character_name}")
    keywords = [row[0] for row in cursor.fetchall()]   #json格式
    keyword=[]
    for i in range(len(keywords)):
        for j in range(len(keywords[i])):
            keyword.append(keywords[i][j])
    keyword=list(set(keyword))
    cursor.close()
    conn.close()
    return keyword

def find_memory_by_keywords(keyword):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {Prompt.character_name} WHERE memory_content LIKE ?', ('%' + keyword+ '%',))
    memories = cursor.fetchall()
    found_memories=[]
    for memory in memories:
        memory = MemoryNode(memory[0], memory[1], keywords_format(memory[2]), memory[3], memory[4], memory[5], memory[6], memory[7])
        found_memories.append(memory)
    cursor.close()
    conn.close()
    return found_memories

# 更新数据
def update_memory(memory_id, meta_data):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    update_fields = ', '.join([f"{field} = ?" for field in meta_data])
    update_values = tuple(meta_data.values()) + (memory_id,)
    cursor.execute(f"UPDATE {Prompt.character_name} SET {update_fields} WHERE id = ?", update_values,memory_id)
    conn.commit()
    cursor.close()
    conn.close()


def rerank_id():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 创建临时表，用于存储重新编号的记录
    cursor.execute(f'''
        CREATE TEMPORARY TABLE temp_renumbered AS
        SELECT ROW_NUMBER() OVER (ORDER BY id) AS new_id, *
        FROM {Prompt.character_name};
    ''')

    # 删除原表中的所有记录
    cursor.execute(f'''
        DELETE FROM {Prompt.character_name};
    ''')

    # 将重新编号的记录插入原表
    cursor.execute(f'''
        INSERT INTO {Prompt.character_name} (id, memory_content, memory_keywords, role, importance, memory_recall_count, created_time, updated_time)
        SELECT new_id, memory_content, memory_keywords, role, importance, memory_recall_count, created_time, updated_time
        FROM temp_renumbered;
    ''')

    # 删除临时表
    cursor.execute(f'''
        DROP TABLE temp_renumbered;
    ''')

    # 提交更改
    conn.commit()
    cursor.close()
    conn.close()



def clean_memory():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # 删除没有关键词的记忆
    cursor.execute(f'''
        DELETE FROM {Prompt.character_name}
        WHERE memory_keywords IS NULL OR memory_keywords = '[]' ;
    ''')

    # 创建临时表，用于存储唯一的内容和最大 ID
    cursor.execute(f'''
        CREATE TEMPORARY TABLE temp_unique_contents AS
        SELECT MAX(id) AS max_id, memory_content
        FROM {Prompt.character_name}
        GROUP BY memory_content;
    ''')

    # 删除重复的内容，只保留 ID 最大的记录
    cursor.execute(f'''
        DELETE FROM {Prompt.character_name}
        WHERE id NOT IN (SELECT max_id FROM temp_unique_contents);
    ''')

    # 提高剩余唯一记录的重要性
    cursor.execute(f'''
        UPDATE {Prompt.character_name}
        SET importance = importance * 1.5;
    ''')

    # 提交更改
    conn.commit()
    cursor.close()
    conn.close()
    #重新排序号
    rerank_id()



def review_memory(memory_id):
    conn=sqlite3.connect(db_file)
    cursor=conn.cursor()
    # 更新记忆的最后复习时间
    cursor.executemany(f"UPDATE {Prompt.character_name} SET updated_time  = ? , importance = importance * 1.5 WHERE id = ?", [(datetime.now(),memory_id)])
    #cursor.executemany(f"UPDATE {Prompt.character_name} SET last_review_time = ?  WHERE id = ?", [(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),memory_id)])
    conn.commit()
       # 提高剩余唯一记录的重要性

    # 提交更改
    conn.commit()
    cursor.close()
    conn.close()




def detect_character(target_name):
    target_file=db_dir+'/'+target_name+'.db'
    if os.path.exists(target_file):
        return True
    else:
        Prompt.character_name=target_name
        create_charater_memory()

def create_charater_memory():
    try:
        init_db()
        # 主逻辑
    
        meta_datas = []
        create_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 读取JSONl文件
        dialog_dict = []
        with open(meta_file, 'r',encoding='utf-8') as file:
            # 逐行读取并解析
            for line in file:
                dialog_dict.append(json.loads(line))
        # 将读取的数据转换为JSON格式
        json_data = json.dumps(dialog_dict, ensure_ascii=False, indent=4)

        # 将JSON数据写入目标文件
        with open(target_file, 'w', encoding='utf-8') as out_file:
            out_file.write(json_data)
                    
                    
        for item in dialog_dict:
            #如果存在prompt字段，则添加到记忆库中
            if "prompt" in item:
                # 提取用户发言的信息
                meta_data = {
                    "content": item["prompt"],
                    "keywords": KeyWord.extract_keywords(item["prompt"]),
                    "importance": 0.5,
                    "role": 'user',
                    "recall_count": 1,
                    "created_time": create_time,
                    "updated_time": create_time
                }
                add_memory(meta_data)
                meta_datas.append(meta_data)

            if "completion" in item:
                # 提取助手发言的信息
                meta_data = {
                    "content": item["completion"],
                    "keywords": KeyWord.extract_keywords(item["completion"]),
                    "importance": 0.5,
                    "role": 'assistant',
                    "recall_count": 1,
                    "created_time": create_time,
                    "updated_time": create_time
                }
                add_memory(meta_data)
                meta_datas.append(meta_data)

        # 写入文件
        with open(output_folder + f'/{Prompt.character_name}_memory.json', 'w') as file:
            json.dump(meta_datas, file, indent=4)
        print("角色记忆库初始化完成")
    except Exception as e:
        print("初始化角色失败",e)


#数据库到文本
def export_db_to_text():
    detect_archive_db()
    conn = sqlite3.connect(archive_db_file)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {Prompt.character_name}")
    rows=cursor.fetchall()
    #json格式
    for row in rows:
        memory=MemoryNode(row[0], row[1], json.loads(row[2]), row[3], row[4], row[5], row[6], row[7])
        # 定义一个正则表达式模式，用于匹配非中文字符
        # 这里假设非中文字符包括英文字母、数字和标点符号
        pattern = r"[^\u4e00-\u9fa5]"

        # 使用正则表达式替换匹配到的非中文字符
        memory.content = re.sub(pattern, "", memory.content)
        m_json={
            "id":memory.id,
            "content":memory.content,
            "keywords":memory.keyword,
            "role":memory.role,
            "importance":memory.importance,
            "memory_recall_count":memory.memory_recall_count,
            "created_time":memory.created_time,
            "last_review_time":memory.last_review_time
        }
        with open(output_folder + f'/{Prompt.character_name}_memory.json', 'a', encoding='utf-8') as file:
            json.dump(m_json, file, ensure_ascii=True, indent=4)
    cursor.close()
    conn.close()
    print("导出成功")