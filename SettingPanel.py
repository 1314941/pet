import sys
import random
from PySide6.QtCore import Signal,QEvent,QTimer,QObject,QRect,QPoint,QSize
from PySide6.QtWidgets import QWidget,QMenu,QPushButton,QSystemTrayIcon,QLabel,QVBoxLayout,QHBoxLayout,QLineEdit,QFrame,QScrollArea,QFileDialog
from PySide6.QtGui import QAction,QIcon,Qt
import shutil
import os
import logging
from datetime import datetime
import math
from WaterfallLayout import WaterfallLayout
from ChatPanel import ChatBubble,ChatPanel
import Port
import tts
root_file=os.path.abspath(os.path.dirname(__file__))

current_time = datetime.now().strftime("%Y%m%d")
# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


class SettingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=None)
        self.initUI()
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        # 创建一个列表组件
        self.setting_list_widget = WaterfallLayout(1)


        #标签  角色预设
        #声音合成
        self.character_label = QLabel("角色扮演", self)
        self.character_label.setAlignment(Qt.AlignCenter)
        self.prompt_label = QLabel("角色预设", self)
        #文件选择按钮
        self.prompt_button = QPushButton("选择文件", self)
        self.prompt_button.clicked.connect(self.select_prompt_file)
        self.prompt_layout = QHBoxLayout()
        self.prompt_layout.addWidget(self.prompt_label)
        self.prompt_layout.addWidget(self.prompt_button)

        #输入框  可换行 滑动
        self.prompt_edit = QLineEdit(self)
        self.prompt_edit.setPlaceholderText("请输入角色预设")
        self.prompt_edit.setMinimumHeight(100)

        # 添加标签和输入框
        #端口设置名
        self.port_label=QLabel("端口设置", self)
        self.port_label.setAlignment(Qt.AlignCenter)
        self.port_setting_name_label = QLabel("端口设置名:", self)
        self.port_setting_name_line = QLineEdit(self)
        self.port_setting_name_line.setPlaceholderText(Port.name)
        self.ollama_port_label = QLabel("Ollama 端口:", self)
        self.ollama_port_edit = QLineEdit(self)
        self.ollama_port_edit.setText(str(Port.ollama_port))

        self.ollama_command_label = QLabel("Ollama 命令:", self)
        self.ollama_command_edit = QLineEdit(self)
        self.ollama_command_edit.setText(Port.ollama_command)

        self.gpt_sovits_port_label = QLabel("GPT-SoVITS 端口:", self)
        self.gpt_sovits_port_edit = QLineEdit(self)
        self.gpt_sovits_port_edit.setText(str(Port.gpt_sovits_port))

        self.gpt_sovits_path_label = QLabel("GPT-SoVITS 项目文件夹:", self)
        self.gpt_sovits_path_edit = QLineEdit(self)
        self.gpt_sovits_path_edit.setText(Port.gpt_sovits_path)
        self.gpt_sovits_path_button = QPushButton("选择文件夹", self)
        self.gpt_sovits_path_button.clicked.connect(self.select_gpt_sovits_path)
        self.gpt_sovits_path_button.setToolTip("选择 GPT-SoVITS 项目文件夹")
        self.gpt_sovits_path_layout=QHBoxLayout()
        self.gpt_sovits_path_layout.addWidget(self.gpt_sovits_path_label)
        self.gpt_sovits_path_layout.addWidget(self.gpt_sovits_path_button)
   
        #gpt_weights
        self.gpt_weights_label = QLabel("GPT_WEIGHTS 权重文件:", self)
        self.gpt_weights_edit = QLineEdit(Port.gpt_weights, self)
        self.gpt_weights_edit.setPlaceholderText("请输入权重文件路径")
        self.gpt_weights_button=QPushButton("选择文件", self)
        self.gpt_weights_button.clicked.connect(self.select_gpt_weights_file)
        self.gpt_weights_layout=QHBoxLayout()
        self.gpt_weights_layout.addWidget(self.gpt_weights_label)
        self.gpt_weights_layout.addWidget(self.gpt_weights_button)
        #SVOITS_WEIGHTS
        self.svoits_wights_label = QLabel("SVOITS_WEIGHTS 权重文件:", self)
        self.svoits_wights_edit = QLineEdit(Port.sovits_weights,self)
        self.svoits_wights_edit.setPlaceholderText("请输入权重文件路径")
        self.svoits_wights_button=QPushButton("选择文件", self)
        self.svoits_wights_button.clicked.connect(self.select_svoits_weights_file)
        self.svoits_wights_layout=QHBoxLayout()
        self.svoits_wights_layout.addWidget(self.svoits_wights_label)
        self.svoits_wights_layout.addWidget(self.svoits_wights_button)

        #参考音频
        self.reference_audio_label = QLabel("参考音频:", self)
        self.reference_audio_edit = QLineEdit(Port.gpt_sovits_voice,self)
        self.reference_audio_button=QPushButton("选择文件", self)
        self.reference_audio_button.clicked.connect(self.select_reference_audio_file)
        self.reference_audio_layout=QHBoxLayout()
        self.reference_audio_layout.addWidget(self.reference_audio_label)
        self.reference_audio_layout.addWidget(self.reference_audio_button)
        #参考文本
        self.reference_text_label = QLabel("参考文本:", self)
        self.reference_text_edit = QLineEdit(Port.gpt_sovits_text,self)
        self.reference_text_button=QPushButton("选择文件", self)
        self.reference_text_button.clicked.connect(self.select_reference_text_file)
        self.reference_text_layout=QHBoxLayout()
        self.reference_text_layout.addWidget(self.reference_text_label)
        self.reference_text_layout.addWidget(self.reference_text_button)
        #语言
        self.language_label = QLabel("语言:", self)
        self.language_edit = QLineEdit(Port.gpt_sovits_language,self)

        self.setting_list_widget.add_widget(self.character_label)
        self.setting_list_widget.add_widget(self.prompt_layout)
        self.setting_list_widget.add_widget(self.prompt_edit)
        self.setting_list_widget.add_widget(self.port_label)
        self.setting_list_widget.add_widget(self.port_setting_name_label)
        self.setting_list_widget.add_widget(self.port_setting_name_line)
        self.setting_list_widget.add_widget(self.ollama_port_label)
        self.setting_list_widget.add_widget(self.ollama_port_edit)
        self.setting_list_widget.add_widget(self.ollama_command_label)
        self.setting_list_widget.add_widget(self.ollama_command_edit)
        self.setting_list_widget.add_widget(self.gpt_sovits_port_label)
        self.setting_list_widget.add_widget(self.gpt_sovits_port_edit)
        self.setting_list_widget.add_widget(self.gpt_sovits_path_layout)
        self.setting_list_widget.add_widget(self.gpt_sovits_path_edit)
        self.setting_list_widget.add_widget(self.gpt_weights_layout)
        self.setting_list_widget.add_widget(self.gpt_weights_edit)
        self.setting_list_widget.add_widget(self.svoits_wights_layout)
        self.setting_list_widget.add_widget(self.svoits_wights_edit)
        self.setting_list_widget.add_widget(self.reference_audio_layout)
        self.setting_list_widget.add_widget(self.reference_audio_edit)
        self.setting_list_widget.add_widget(self.reference_text_layout)
        self.setting_list_widget.add_widget(self.reference_text_edit)
        self.setting_list_widget.add_widget(self.language_label)
        self.setting_list_widget.add_widget(self.language_edit)
        self.scroll_area.setWidget(self.setting_list_widget)

        # 使用 QVBoxLayout 来居中 QScrollArea
        self.setting_layout = QVBoxLayout(self)
        self.setting_layout.addWidget(self.scroll_area)

        self.layout.addLayout(self.setting_layout)  
        self.show_setting() 
     
    def show_setting(self):
        self.ollama_command_edit.setText(str(Port.ollama_command))
        self.ollama_port_edit.setText(str(Port.ollama_port))
        self.gpt_sovits_path_edit.setText(str(Port.gpt_sovits_path))
        self.gpt_sovits_port_edit.setText(str(Port.gpt_sovits_port))
        self.gpt_weights_edit.setText(str(Port.gpt_weights))
        self.svoits_wights_edit.setText(str(Port.sovits_weights))
        self.reference_audio_edit.setText(str(Port.gpt_sovits_voice))
        self.reference_text_edit.setText(str(Port.gpt_sovits_text))
        self.language_edit.setText(str(Port.gpt_sovits_language))

    def select_prompt_file(self):
        #选择文本文件
        file_path, _ = QFileDialog.getOpenFileName(self, "选择角色预设文件", "", "文本文件 (*.txt)")
        #获取文本内容

        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            self.prompt_edit.setText(text)
            logging.info(f"选择角色预设文件：{file_path}")

    def select_gpt_sovits_path(self):
        #选择GPT-SoVITS项目文件夹
        file_path = QFileDialog.getExistingDirectory(self, "选择GPT-SoVITS项目文件夹", "")
        if file_path:
            self.gpt_sovits_path_edit.setText(file_path)
            logging.info(f"选择GPT-SoVITS项目文件夹：{file_path}")
            Port.gpt_sovits_path=file_path

    def select_gpt_weights_file(self):
        #选择GPT_WEIGHTS权重文件
        file_path, _ = QFileDialog.getOpenFileName(self, "选择GPT_WEIGHTS权重文件", "", "权重文件 (*.pth)")
        if file_path:
            self.gpt_weights_edit.setText(file_path)
            logging.info(f"选择GPT_WEIGHTS权重文件：{file_path}")
            Port.gpt_weights=file_path

    def select_svoits_weights_file(self):
        #选择SVOITS_WEIGHTS权重文件
        file_path, _ = QFileDialog.getOpenFileName(self, "选择SVOITS_WEIGHTS权重文件", "", "权重文件 (*.ckpt)")
        if file_path:
            self.svoits_wights_edit.setText(file_path)
            logging.info(f"选择SVOITS_WEIGHTS权重文件：{file_path}")
            Port.sovits_weights=file_path

    def select_reference_audio_file(self):
        #选择参考音频文件
        file_path, _ = QFileDialog.getOpenFileName(self, "选择参考音频文件", "", "音频文件 (*.wav)")
        if file_path:
            self.reference_audio_edit.setText(file_path)
            logging.info(f"选择参考音频文件：{file_path}")
            Port.gpt_sovits_voice=file_path

    def select_reference_text_file(self):
        #选择参考文本文件
        file_path, _ = QFileDialog.getOpenFileName(self, "选择参考文本文件", "", "文本文件 (*.txt)")
        if file_path:
            #读取文本内容
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            self.reference_text_edit.setText(text)
            Port.gpt_sovits_text=text
            logging.info(f"选择参考文本文件：{file_path}")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
 