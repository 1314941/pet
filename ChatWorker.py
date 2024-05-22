
from PySide6.QtWidgets import QWidget, QGridLayout,QFrame,QScrollArea,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit
from PySide6.QtGui import QPixmap,QFont
from PySide6.QtCore import Signal, Slot,Qt,QUrl
import requests
from datetime import datetime
from chat_database import *
import logging
from openai import OpenAI
import tts
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import ollama
from PySide6.QtCore import QThread, Signal,QObject,QTimer
import time
import asyncio
import aiohttp
import torch
#聊天线程类
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

current_time = datetime.now().strftime("%Y%m%d")

config = XttsConfig()
config.load_json("model/tts/XTTS-v2/config.json")
config['output_path']=os.path.normpath(config['output_path'])+f'/{current_time}'
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir="model/tts/XTTS-v2", eval=True)
#model.cuda()



# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')



class ChatWorker(QObject):
    # 定义一个信号，用于传递条件状态
    show_result_signal = Signal(bool)
    show_content_signal=Signal(str)

    def __init__(self):
        super().__init__()
        self.messages=[]
        self.username='user'
        self.prompt=tts.prompt_text
        self.ref_tts_wav=tts.refer_wav_path
        print("参考音频:",self.ref_tts_wav)
        if self.ref_tts_wav is None:
            self.ref_tts_wav=os.path.normpath(self.ref_tts_wav)
            self.ref_tts_wav=self.ref_tts_wav.replace('\\','/')
            if os.path.exists(self.ref_tts_wav) is False:
                self.ref_tts_wav=None
        print("修改后参考音频:",self.ref_tts_wav)
        self.url='http://localhost:11434/chat'
        #self.model='llama:8b'
        self.model='gemma:7b'

        self.timestamp=''
        self.voice_path=''
        self.chatbox=None
        self.send_message_signal=False
        self.need_send_message=False

        self.timer=QTimer()
        self.timer.timeout.connect(self.watting)

    def format_input(self):
        pass  #处理输入，添加进数据库
    

    def watting(self):
        if self.need_send_message:
            self.send_message() 


    def send_message(self):
        # Chat with an intelligent assistant in your terminal

        # Point to the local server
        if self.message:
            try:
                print("开始发送消息")
                client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

                self.history = [
                    {"role": "system", "content": self.prompt},
                ]
                self.history.append({"role": "user", "content": self.message})

                while True:
                    completion = client.chat.completions.create(
                        model="publisher/Repository",
                        messages=self.history,
                        temperature=0.7,
                        stream=True,
                    )

                    new_message = {"role": "assistant", "content": ""}
                    
                    for chunk in completion:
                        if chunk.choices[0].delta.content:
                            print(chunk.choices[0].delta.content, end="", flush=True)
                            new_message["content"] += chunk.choices[0].delta.content
                            self.show_content_signal.emit(new_message["content"])
                    self.get_message(new_message["content"])
                    self.history.append(new_message)
            except Exception as e:
                print(f"Error: {e}  LmStudio Api出错啦")



    def get_message(self, response):
        try:
            if response:
                print("开始生成语音")
                message=response
                self.messages.append({'role': 'assistant', 'content': message})
                self.timestamp=datetime.now().strftime("%Y-%m-%d")
                self.voice_path=self.generate_voice(message,self.timestamp)
                self.message=message
                self.show_result_signal.emit(True)
                add_chat(self.username,self.model,message,self.voice_path,self.timestamp)
            else:
                self.voice_path=self.generate_voice("抱歉，我无法理解你的意思")
                self.show_result_signal.emit(False)
            self.need_send_message=False   #停止发送消息
            #只保留最新的四条历史谈话
            while len(self.messages) > 4:
                self.messages.pop(0)
        except Exception as e:
            print("发送语音失败: %s" % str(e))
            logging.exception("发送请求失败: %s", str(e))
        

  





#生成语音   无法保存语音啊
    def generate_voice(self,text,timestamp=datetime.now().strftime("%Y-%m-%d")):
        try:
            if self.ref_tts_wav is None or os.path.exists(self.ref_tts_wav) is False:
                print('参考音频路径不能为空')
                return None
            #保留文本前五个子作为文件名
            file_text=text[:5]          #修改一下  提取内容 作为称呼  
            root_path='tts/out'
            if not os.path.exists(root_path):
                os.mkdir(root_path)
            voice_dir=f'{root_path}/{timestamp}'
            if not os.path.exists(voice_dir):
                os.mkdir(voice_dir)
            voice_path=f'{root_path}/{timestamp}/{file_text}_{timestamp}.wav'
            voice_path=os.path.normpath(voice_path)
            #生成语音
            outputs = model.synthesize(
                "It took me quite a long time to develop a voice and now that I have it I am not going to be silent.",
                config,
                speaker_wav=self.ref_tts_wav,
                gpt_cond_len=3,
                language="zh-cn",
            )
            print(f'音频已保存为{voice_path}.wav')
            return voice_path
        except Exception as e:
            print(f'生成语音失败: {e}')
            return None








'''  

 #不知道咋设置角色扮演
    def send_message_ollama(self,messages):
        if messages:
            try:
                print("开始发送消息")
                stream=ollama.chat(
                model=self.model,     #好像没法角色扮演
                messages=self.messages,
                stream=True
                )
                #将chunks流式处理为字符串
                response = ""
                for chunk in stream:
                    response += chunk['message']['content']
                    self.chatbox.set_text(response)
                self.get_message(response)
            except ollama.ResponseError as e:
                print('Error:', e.error)
                if e.status_code == 404:
                    ollama.pull(self.model)





  
    #生成语音   每次都开端口  有点麻烦  还需要整合包
    def generate_voice(self,text,timestamp=datetime.now().strftime("%Y-%m-%d")):
        try:
            # GPT-SoVITS API的URL和端口
            url = 'http://127.0.0.1:9881'

            # 参考音频的路径（相对路径或绝对路径，取决于你的GPT-SoVITS服务配置）
            #refer_wav_path = 'C:\chat\gpt_sovits\GPT-SoVITS-beta0306fix2\GPT-SoVITS-beta0306fix2\DATA\audio\longzu\slicers\good.wav'

            # 提示文本
            prompt_text = '你好，世界'

            # 提示文本的语言
            prompt_language = 'zh'

            # 要合成的文本
            text = text

            # 文本的语言
            text_language = 'zh'

            # 构建请求参数
            data = {
                #'refer_wav_path': refer_wav_path,
                'prompt_text': prompt_text,
                'prompt_language': prompt_language,
                'text': text,
                'text_language': text_language
            }

            # 发送POST请求
            response = requests.post(url, json=data)
            # 检查响应状态码
            if response.status_code == 200:
                #保留文本前五个子作为文件名
                file_text=text[:5]          #修改一下  提取内容 作为称呼  
                root_path='voice'
                if not os.path.exists(root_path):
                    os.mkdir(root_path)
                voice_dir=f'{root_path}/{timestamp}'
                if not os.path.exists(voice_dir):
                    os.mkdir(voice_dir)
                voice_path=f'{root_path}/{timestamp}/{file_text}_{timestamp}.wav'
                voice_path=os.path.normpath(voice_path)
                # 如果响应状态码为200，表示成功，将音频流保存到文件
                with open(voice_path, 'wb') as f:
                    f.write(response.content)
                print(f'音频已保存为{voice_path}.wav')
                return voice_path
            else:
                # 如果响应状态码不是200，表示失败，输出错误信息
                print('请求失败:', response.status_code)
                print('错误信息:', response.text)
                #返回音频地址 
                return None
        except Exception as e:
            print(f'生成语音失败: {e}')
            return None
'''