import Port
import tts
import ActionPanel
from PySide6.QtWidgets import QWidget, QGridLayout,QFrame,QScrollArea,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit
from PySide6.QtGui import QPixmap,QFont
from PySide6.QtCore import Signal, Slot,Qt,QUrl
import requests
from datetime import datetime
from chat_database import *
from ChatWorker import ChatWorker
import logging
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import ollama
from PySide6.QtCore import QThread, Signal,QObject,QTimer
import time
import random
from Emotion import EmotionAssistant


current_time = datetime.now().strftime("%Y%m%d")
# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

#吃 抬 摸头 喝  说 开始 结束   有几个忘记加上去了
actions=['eat','lift','pat','drink','say','start','end']

#情绪状态类
class MoodWorker(QObject):
    #发送动作触发信号
    show_action_signal = Signal(str)
    interact_signal=Signal(str)
    def __init__(self,action_panel):
        super().__init__()
        try:
            self.action_window=action_panel
            self.emtionassistant=EmotionAssistant()
            self.init_data()
            self.start_timer()
        except Exception as e:
            # 如果初始化失败，打印错误信息
            logging.error("初始化失败: %s", str(e))
            print("初始化失败: %s" % str(e))
    

    def init_player(self):
        try:
            # 创建一个 QMediaPlayer 实例
            self.player = QMediaPlayer()
            # 创建一个 QAudioOutput 实例并将其设置给 QMediaPlayer
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
        except Exception as e:
            # 如果初始化失败，打印错误信息
            logging.error("QMediaPlayer 初始化失败: %s", str(e))
            print("QMediaPlayer 初始化失败: %s" % str(e))

    def init_data(self):
        try:
            self.action_messages=[]
            self.username='user'
            self.url='http://localhost:11434/chat'
            #self.model='llama:8b'
            self.model='gemma:7b'

            self.chatdialog=None

            self.voice_path=''
            self.action_signal=False

            self.need_action_signal=False         #启动信号
            self.actioning_signal=False
            self.updating_action=False
            self.getting_action=False
            #动作
            self.nomal_actions=self.action_window.right_panel.get_nomal_actions()  #由于历史遗留问题，取名有点诡异 感觉以后会被自己坑到
            self.interact_action=None
            self.raise_action=self.action_window.interact_panel.find_matching_actions('抬')
            self.interact_actions={action:[] for action in actions}
            for action in actions:
                result=self.action_window.interact_panel.find_matching_actions(action)
                if result==None:
                    print(action+' not found')
                else:
                    self.interact_actions[action]=result
            #随机性
            self.probability=0.5
            #心情
            self.mood=100
            self.hungry=0
            self.thirsty=0
            self.boring=0
            self.sick=0

            self.timestamp='' 
        # 心情字典
            self.moods = {
                'happy': '我笑了啊',        # 快乐
                'normal': '我是毫无感情的杀手',  # 正常
                'poorcondition': '我哭的梨花带雨',       # 悲伤
                'ill':'我大概是要去见阎王啦'  
            }
            self.mood_state='happy'     #唯一

        except Exception as e:
            print(f"初始化数据异常, 错误信息: {e}")
            logging.exception(f"初始化数据异常, 错误信息: {e}")
      
    def start_timer(self):
        self.moodtimer=QTimer()
        self.moodtimer.setInterval(10000)
        self.moodtimer.timeout.connect(self.updateState)
        self.moodtimer.start()


    def eat(self):
        print("吃东西")
        self.interact_action=self.action_window.interact_panel.find_matching_actions('eat')
        self.interact_signal.emit('吃')
        # 删除桌面上的所有txt文件
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        for filename in os.listdir(desktop_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(desktop_path, filename)
                try:
                    os.remove(file_path)
                    print(f"File {filename} deleted.")
                    self.hungry-=30   #减少饥饿值
                  
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")

    def drink(self):
        print("喝水")
        self.interact_action=self.action_window.interact_panel.find_matching_actions('drink')
        self.interact_signal.emit('喝')
        # 删除桌面上的所有txt文件
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        for filename in os.listdir(desktop_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(desktop_path, filename)
                try:
                    os.remove(file_path)
                    print(f"File {filename} deleted.")
                    self.thirsty-=30   #减少饥饿值
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")
    
    def updateState(self):
        self.need_action_signal=False
        self.mood-=1
        print("心情值：",self.mood)
        if self.mood>100:
            self.mood=100
        elif self.mood==0:
            self.mood=1

        if self.mood<=50:
            self.mood_state='poorcondition'
        elif self.mood>50 and self.mood<=70:
            self.mood_state='normal'
        elif self.mood>70 and self.mood<100:
            self.mood_state='happy'
        
        if self.hungry>100:
            self.hungry=100
        elif self.hungry<=0:
            self.hungry=1
        if self.thirsty>100:
            self.thirsty=100
        elif self.thirsty<=0:
            self.thirsty=1


        if self.hungry>=50:
            if self.hungry>70 and self.actioning_signal==False:
                self.need_action_signal=True
            self.hungry-=random.randint(1,10)
        else:
            self.eat()
            if self.hungry<=50 and self.actioning_signal==False:
                self.need_action_signal=True
            return
        if self.thirsty>=50:
            self.thirsty-=random.randint(1,10)
        else:
            self.drink()
            if self.actioning_signal==False:
                self.need_action_signal=True

    def action_if_need(self):
        #return
        if self.need_action_signal:
            self.actioning_signal=True
            self.need_action_message=False
            #随机播放语音 生成一个随机数 大于0.7则播放语音
            if random.random() > 0.7:
                print("正在选择对话")
                #从状态列表随机获取一个模式
                mood=self.mood_state
                event_state=random.choice(list(self.event_state.keys()))
                for event,value in self.event_state.items():
                    if value==1 and random.random()>self.probability:
                        event_state=event
                self.action_message=f'如果有人{mood}和{event_state},如果你处于她那样的心情，作为一个傲娇又搞笑的女孩子，你会如何通过言语表达你的心情（只需要回复你的选择，不用介绍原因）？'
                print("开始接入聊天接口")
                self.choose_message()
            else:
                self.action_message=''

    def play_voice(self):
        if self.voice_path !=None:
            self.player.setSource(QUrl.fromLocalFile(self.voice_path))
            self.player.play()

    def choose_message(self):
        if Port.gpt_port_signal==False:  #接口未开启
            print("文本生成接口未开启")
            return 
        print("开始生成文本")
        if self.action_message!=''and self.action_message!=None:
            try:
                print("开始发送消息")
                stream=ollama.chat(
                model=self.model,
                messages=self.action_messages,
                stream=True
                )
                #将chunks流式处理为字符串
                response = ""
                for chunk in stream:
                    response += chunk['message']['content']
                    self.chatdialog.set_text(response)
                self.get_message(response)
                self.assistant_message=self.emtionassistant.get_most_similar_sentence()
            except ollama.ResponseError as e:
                print('Error:', e.error)
                if e.status_code == 404:
                    ollama.pull(self.model)

         
    def get_message(self, response):
        try:
            if response:
                print(response)
                message=response
                self.messages.append({'role': 'assistant', 'content': message})
                self.timestamp=datetime.now().strftime("%Y-%m-%d")
                self.voice_path=self.generate_voice(message,self.timestamp)
                self.message=message
                self.action_signal.emit('true')
                add_chat(self.username,self.model,message,self.voice_path,self.timestamp)
            else:
                self.message="抱歉，我无法理解你的意思"
                self.voice_path=self.generate_voice(self.message)
                self.action_signal.emit('false')   #所有工作准备完毕  开始执行
            self.play_voice()
            self.talkpanel.setText(self.message)
            self.talkpanel.show()
            self.need_action_message=False   #停止发送消息
            #只保留最新的四条历史谈话
            while len(self.action_messages) > 4:
                self.action_messages.pop(0)
        except Exception as e:
            print("发送语音失败: %s" % str(e))
            logging.exception("发送请求失败: %s", str(e))
        

    #生成语音
    def generate_voice(self,text,timestamp=datetime.now().strftime("%Y-%m-%d")):
        try:
            if Port.voice_port_signal==False:
                print("语音生成接口未开启")
                return None
            print("开始生成语音")
            # GPT-SoVITS API的URL和端口
            url = 'http://127.0.0.1:9881'

            # 参考音频的路径（相对路径或绝对路径，取决于你的GPT-SoVITS服务配置）
            #refer_wav_path = 'C:\chat\gpt_sovits\GPT-SoVITS-beta0306fix2\GPT-SoVITS-beta0306fix2\DATA\audio\longzu\slicers\good.wav'

            # 提示文本
            prompt_text = tts.prompt_text

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
                file_text=text[:5]
                root_path='voice'
                if not os.path.exists(root_path):
                    os.mkdir(root_path)
                voice_path=f'{root_path}/{file_text}_{timestamp}.wav'
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

'''
  # 事件字典
        self.events = {
            'default': '今天又是元气满满的一天！',  # 默认
            'health': '今天又是元气满满的一天！',    # 健康
            'full': '还有些东西没吃',            # 饱腹
            'hungry': '姐要吃饭饭',            # 饥饿
            'thirsty': '水,水,水',             # 口渴
            'boring': '躺尸',                 # 无聊
            'gaming': '我要开黑',              # 开黑
            'sick': '我大概是病了，病的还不轻'     # 生病
        }
'''