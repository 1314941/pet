import sys

sys.path.append('..')
from relext import RelationExtraction


# 文件路径
prompt_path = 'prompt/meimo.txt'  # 替换为你的文本文件路径

# 打开文件并读取内容
with open(prompt_path, 'r', encoding='utf-8') as file:
    prompt_text = file.read()
article = prompt_text
m = RelationExtraction()
triples = m.extract(article)
print(triples)

import re

# 假设这是你的文本
text = "这是一个包含非中文的文本，例如英文和数字：Hello, 123456！"

# 定义一个正则表达式模式，用于匹配非中文字符
# 这里假设非中文字符包括英文字母、数字和标点符号
pattern = r"[^\u4e00-\u9fa5]"

# 使用正则表达式替换匹配到的非中文字符
cleaned_text = re.sub(pattern, "", text)

print(cleaned_text)