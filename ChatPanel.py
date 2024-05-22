from PySide6.QtWidgets import QWidget, QGridLayout,QFrame,QScrollArea,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTextEdit,QLineEdit
from PySide6.QtGui import QPixmap,QFont
from PySide6.QtCore import Signal, Slot,Qt,QUrl
import requests
from datetime import datetime
from chat_database import *
from ChatWorker import ChatWorker
from WaterfallLayout import WaterfallLayout
import logging
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import ollama
from PySide6.QtCore import QThread, Signal,QObject,QTimer
import time
import asyncio
import aiohttp


current_time = datetime.now().strftime("%Y%m%d")
# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


class ChatBubble(QWidget):
    play_clicked=Signal(str)
    def __init__(self, text,voice_path, is_me=False, parent=None):
        super(ChatBubble, self).__init__(parent)
        self.playable=False  #默认没有播放按钮
        self.initUI(text,voice_path, is_me)

    def initUI(self, text,voice_path, is_me):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 创建头像标签
        avatar_label = QLabel(self)
        avatar_pixmap = QPixmap("6.png")  # 替换为头像图片路径
        avatar_label.setPixmap(avatar_pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        avatar_label.setFixedSize(50, 50)

      # 创建 QTextEdit
        self.text_line = QTextEdit(self)
        self.text_line.setReadOnly(True)  # 设置为只读模式
        self.text_line.setFont(QFont("Arial", 12))
        if text:
            self.text_line.setText(text)

       
        # 根据是谁的信息，决定布局方向
        if is_me:
             #如果音频文件存在，则添加播放按钮
            if voice_path=='wait':
                self.play_button = QPushButton("等待",self)
                self.playable=True
                self.layout.addWidget(self.play_button)

            self.layout.addWidget(self.text_line)
            self.layout.addWidget(avatar_label)
            self.text_line.setStyleSheet("background-color: lightBlue; padding: 5px;")
        else:
            self.layout.addWidget(avatar_label)
            self.layout.addWidget(self.text_line)

             #如果音频文件存在，则添加播放按钮
            if voice_path=='wait':
                self.play_button = QPushButton("等待",self)
                self.playable=True
                self.layout.addWidget(self.play_button)
            self.text_line.setStyleSheet("background-color: lightGreen; padding: 5px;")

        self.setLayout(self.layout)

    def set_voice_path(self,voice_path):
        if self.playable:
            if voice_path!=None and os.path.exists(voice_path):
                    #改为播放
                    self.play_button.setText("播放")
                    #播放图标  自带的
                    self.play_button.clicked.connect(lambda: self.play_voice(voice_path))

    def play_voice(self,voice_path):
        self.play_clicked.emit(voice_path)
        #播放本地音频

    def set_text(self,text):
        self.text_line.setText(text)




class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super(ChatPanel, self).__init__(parent)
       
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
        self.initUI()

        self.start_thread()

    def initUI(self):
        self.setWindowTitle('聊天面板')
        self.layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        # 创建一个列表组件
        self.chat_list_widget = WaterfallLayout(1)
        self.scroll_area.setWidget(self.chat_list_widget)

        # 使用 QVBoxLayout 来居中 QScrollArea
        self.chat_layout = QVBoxLayout(self)
        self.chat_layout.addWidget(self.scroll_area)

         # 创建一个输入框
        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("请输入消息...")
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.setFixedHeight(50)
        self.send_btn=QPushButton("发送")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setFixedHeight(50)
        self.send_layout=QHBoxLayout()
        self.send_layout.addWidget(self.input_box)
        self.send_layout.addWidget(self.send_btn)

        self.layout.addLayout(self.send_layout)
        self.layout.addLayout(self.chat_layout)        
        # 添加聊天泡泡
        self.chatbox=ChatBubble("你好！",None, False)
        self.chat_list_widget.add_widget(self.chatbox)
        # ... 添加更多的聊天泡泡 ...


    def start_thread(self):
        try:
            self.thread = QThread()
            self.worker = ChatWorker()
            self.worker.show_result_signal.connect(self.show_result)
            self.worker.show_content_signal.connect(self.chatbox.set_text)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.timer.start)
            self.thread.start()
        except Exception as e:
            print("启动线程失败: %s" % str(e))

    def play_voice(self,voice_path):
        self.player.setSource(QUrl.fromLocalFile(voice_path))
        self.player.play()


    def send_message(self):
        try:
            message = self.input_box.text()
            self.send_btn.setEnabled(False)  #不能发送
            if message:
                #时间戳
                add_chat_time=datetime.now().strftime("%Y-%m-%d")
                chatbox=ChatBubble(message,"wait", is_me= True)
                voice_path=self.worker.generate_voice(message,add_chat_time)
                add_chat("user","llama:8b",message,voice_path,add_chat_time)
                chatbox.set_voice_path(voice_path)    #可以播放语音
                self.play_voice(voice_path=voice_path)
                chatbox.play_clicked.connect(self.play_voice)
                self.chat_list_widget.add_widget(chatbox)
                #self.input_box.clear()
                self.worker.messages.append({'role': self.worker.username, 'content': message})
                self.chatbox=ChatBubble(' ','wait', False)
                self.worker.chatbox=self.chatbox
                self.chat_list_widget.add_widget(self.chatbox)
                self.worker.message=message
                self.worker.need_send_message=True
        except Exception as e:
            logging.error("发送消息失败: %s", str(e))
            print("发送消息失败: %s" % str(e))

 

    @Slot(bool)
    def show_result(self,result):
        if result:
            self.chatbox.set_voice_path(self.worker.voice_path)    #可以播放语音
            self.chatbox.play_clicked.connect(self.play_voice)
            self.play_voice(self.worker.voice_path)
        self.send_btn.setEnabled(True)  #可以发送

    def show(self):
        super().show()



