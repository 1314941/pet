default_prompt = '你是我的好朋友，与我从小一起长大,是个文静的女孩子'
prompt_text=None
# 文件路径
prompt_path = 'prompt/paimeng.txt'  # 替换为你的文本文件路径


max_help_tokens=100

#一个很好的助手
system_prompt='你是我的得力助手，能根据我的需求做出完美且正确的回答'

#对话  关系提取  图数据库   风格检测  发起对话 


action_prompt='你是我的好朋友，与我从小一起长大,是个文静的女孩子'


# 打开文件并读取内容
with open(prompt_path, 'r', encoding='utf-8') as file:
    prompt_text = file.read()

character_name='xiaobai'