import os
name='one'
 # GPT-SoVITS API的URL和端口
url = 'http://127.0.0.1:9881'

# 参考音频的路径（相对路径或绝对路径，取决于你的GPT-SoVITS服务配置）
refer_wav_path = 'C:/User/xiaobai/Desktop/pet/tts/in/good.wav'  
#我吐了呀，为啥改了还没变过来，难道还要重启一下vscode吗 好吧，服了，没改数据库的原因

prompt_text = '你是我的好朋友，与我从小一起长大，是个大大咧咧的人。'
# 文件路径
prompt_path = 'memory/prompt/paimeng.txt'  # 替换为你的文本文件路径

# 打开文件并读取内容
with open(prompt_path, 'r', encoding='utf-8') as file:
    prompt_text = file.read()


# 提示文本的语言
prompt_language = 'zh'

# 要合成的文本
text = '讲个笑话'

# 文本的语言
text_language = 'zh'




