from neo4j import GraphDatabase
from transformers import BertModel, BertTokenizer
from annoy import AnnoyIndex
import torch

# 连接到Neo4j图数据库
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# 加载预训练的BERT模型
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

# 初始化向量索引
f = 768  # BERT嵌入向量的维度
t = AnnoyIndex(f, 'dot')  

# 定义Cypher查询函数
def create_pet(tx, name, gender, personality):
    tx.run("CREATE (p:Pet {name: $name, gender:$gender, personality: $personality})", name=name, gender=gender, personality=personality)

def add_memory(tx, pet_name, concept_name, fact_content):
    tx.run("MATCH (p:Pet) WHERE p.name = $pet_name "
           "CREATE (c:Concept {name: $concept_name}) "
           "CREATE (p)-[:HAS_MEMORY]->(c) "
           "CREATE (f:Fact {content: $fact_content}) "
           "CREATE (c)-[:RELATED_TO]->(f)", pet_name=pet_name, concept_name=concept_name, fact_content=fact_content)

def find_memory(tx, pet_name, concept_name):
    return tx.run("MATCH (p:Pet {name: $pet_name})-[:HAS_MEMORY]->(c:Concept {name:$concept_name}) "
                  "RETURN c.name AS concept, f.content AS fact", pet_name=pet_name, concept_name=concept_name).data()

# 创建宠物节点
with driver.session() as session:
    session.write_transaction(create_pet, "Buddy", "Male", "Playful")

# 添加记忆
with driver.session() as session:
    session.write_transaction(add_memory, "Buddy", "greeting", "Hello, how are you?")

# 查找记忆
with driver.session() as session:
    memories = session.read_transaction(find_memory, "Buddy", "greeting")
    print(memories)

# 计算向量表示并构建索引
base_memories = ["Hello, how are you?", "I'm fine, thank you!"]
for i, text in enumerate(base_memories):
    input_ids = tokenizer(text, return_tensors='pt')['input_ids']
    with torch.no_grad():
        embedding = model(input_ids)[0][0].numpy()
    t.add_item(i, embedding)

t.build(10)  # 构建树，树的数量可以根据实际情况调整

# 记忆检索
def retrieve_memory(user_input):
    input_ids = tokenizer(user_input, return_tensors='pt')['input_ids']
    with torch.no_grad():
        query_embedding = model(input_ids)[0][0].numpy()
    
    # 检索最近邻
    nearest_neighbors = t.get_nns_by_vector(query_embedding, 3)
    return [base_memories[i] for i in nearest_neighbors]

# 示例交互
user_input = "How are you?"
matched_memories = retrieve_memory(user_input)
print(matched_memories)

# 关闭数据库连接
driver.close()
