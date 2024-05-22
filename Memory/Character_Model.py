from neomodel import (config, StructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, RelationshipTo,FloatProperty,DateTimeProperty,Relationship)
import uuid
from datetime import datetime


config.DATABASE_URL = 'bolt://neo4j:12345678@localhost:7687'


class Character():
    def __init__(self, name='xiaobai', age='18', gender='male', species='human', ability='sleep', work='assistant'):
        self.name = name
        self.age = age
        self.gender = gender
        self.species = species
        self.ability = ability
        self.work = work



class Memory():
    def __init__(self, content,role='assistant', importance=0.5, recall_count=1, created_time=datetime.now(), updated_time=datetime.now()):
        self.content = content
        self.role=role
        self.importance = importance
        self.recall_count = recall_count
        #如果是字符串，转换为datetime
        if isinstance(created_time,str):
            created_time=datetime.strptime(created_time,'%Y-%m-%d %H:%M:%S')
        if isinstance(updated_time,str):
            updated_time=datetime.strptime(updated_time,'%Y-%m-%d %H:%M:%S')
        self.created_time = created_time
        self.updated_time = updated_time


# 定义角色节点类
class CharacterNode(StructuredNode):
    name = StringProperty(required=True)
    age = IntegerProperty()
    gender = StringProperty()
    species=StringProperty()
    ability=StringProperty()
    work=StringProperty()
    friends = RelationshipTo('Character', 'FRIENDS')  # 角色之间的关系
    remember=RelationshipTo('MemoryNode', 'REMEMBER')  # 角色与记忆的关系
   

# 定义记忆节点类
class MemoryNode(StructuredNode):
    uid = UniqueIdProperty()
    role=StringProperty()
    content = StringProperty(required=True)
    importance = FloatProperty()
    recall_count = IntegerProperty()
    created_time = DateTimeProperty()
    updated_time = DateTimeProperty()
    #记忆与记忆的关系
    related=Relationship('MemoryNode', 'RELATED', model=None)
    remembered = RelationshipTo(CharacterNode, 'REMEMBERED')  # 角色与记忆的关系


# 太麻烦了  
def detect_character(name):
    #查询角色是否存在 
    memories = CharacterNode.nodes.all()
    count=0
    duplicates=[]
    for memory in memories:
        if memory.name==name:
            count+=1
            duplicates.append(memory)
    if count!=0:
        inputs=input("角色已存在,是否删除？(y/n):")
        if inputs=='y':
            for i, duplicate in enumerate(duplicates):
                    print("删除角色：",duplicate.name)
                    #角色记忆
                    memories=duplicate.remebered.all()
                    for memory in memories:
                        print("记忆：",memory.content,"\n")
                    inputs=input("是否删除角色：")
                    if inputs=='y':
                        duplicate.delete()
                    else:
                        continue
            else:
                return False
    return True
  



def create_character(character):
    #查询角色是否存在    不知为啥 unique_index=True 无效
    detect_character(character.name)
    charaternode=CharacterNode.nodes.get_or_none(name=character.name)
    if charaternode:
        return charaternode
    charaternode=CharacterNode(name=character.name,age=character.age,gender=character.gender,species=character.species,ability=character.ability,work=character.work).save()
    return charaternode

def create_memory(characterNode,memory):
    try:
        content = memory.content
        importance = memory.importance
        recall_count = 1
        role=memory.role
        created_time=memory.created_time
        updated_time=memory.updated_time
        memory_id = str(uuid.uuid4())

        memory = MemoryNode(uid=memory_id, content=content,role=role, importance=importance, recall_count=recall_count, created_time=created_time, updated_time=updated_time).save()
        memory.remembered.connect(characterNode)
        characterNode.remember.connect(memory)
        return memory
    except Exception as e:
        print("add memory false",e)
        return None


# 更新角色和记忆
def review_memory(memory_id):
    memory = MemoryNode.nodes.get_or_none(uid=memory_id)
    if memory:
        memory.recall_count += 1
        memory.updated_time = datetime.now()
        memory.importance += 0.1
        memory.save()
        return memory
    return None


# 查找角色的全部记忆
def find_memory_by_character(character_name):
    characterNode = CharacterNode.nodes.get_or_none(name=character_name)
    if characterNode:
        memorynodes = characterNode.remember.all()
        return memorynodes
    return None

def get_memory_content_by_character(character_name):
    characterNode = CharacterNode.nodes.get_or_none(name=character_name)
    if characterNode:
        memorynodes = characterNode.remember.all()
        memory_contents=[]
        for memorynode in memorynodes:
            memory_contents.append(memorynode.content)
        return memory_contents
    return None

#根据角色与记忆内容查找记忆
def find_memory(charater_name:str,content:str):
        memory=MemoryNode.nodes.get_or_none(role=charater_name,content=content)
        if memory:
            return memory
        return None

# 定义数据清洗函数
def clean_character_data(character):
    # 假设我们想要去除角色的名字中的空格，并将名字转换为小写
    character.name = character.name.strip().lower()
    # 其他清洗逻辑...
    character.save()

def clean_memory_data(memory):
    # 假设我们想要确保记忆的内容不为空，并且重要性在0到1之间
    if not memory.content:
        memory.delete()  # 如果内容为空，删除该记忆
    else:
        # 创建一个包含所有记忆的列表
        memories = MemoryNode.nodes.all()
        # 检查记忆的 content 是否在列表中出现两次以上
        if memories.filter(content=memory.content).count() > 1:
            memory.delete()  # 如果记忆重复，删除它
            #剩余的记忆重要性加1
            for m in memories:
                if m.content == memory.content:
                    m.importance += 0.1
                    m.save()
        else:
            memory.content = memory.content.strip()
        memory.save()


def clean_all_data():
    # 清洗所有角色节点
    characters = CharacterNode.nodes.all()
    for character in characters:
        clean_character_data(character)

    # 清洗所有记忆节点
    memories = MemoryNode.nodes.all()
    for memory in memories:
        clean_memory_data(memory)




def delete_related_nodes_and_relationships(character):
    # 获取与角色相关的所有节点
    related_nodes = character.remember.all()
    
    # 遍历相关节点，删除它们及其所有关系
    for related_node in related_nodes:
        related_node.delete()



def delete_character(name):
    # 假设你有一个 CharacterNode 实例，你想删除与之相关的所有节点和关系
    character_node = CharacterNode.nodes.get(name=name)  # 替换为你的角色节点实例
    delete_related_nodes_and_relationships(character_node)
