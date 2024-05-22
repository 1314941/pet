import sys
import random
from PySide6.QtCore import Signal,QEvent,QTimer,QObject,QRect,QPoint,QSize
from PySide6.QtWidgets import QWidget,QMenu,QPushButton,QSystemTrayIcon,QLabel,QVBoxLayout,QHBoxLayout,QLineEdit,QFrame,QScrollArea
from PySide6.QtGui import QAction,QIcon,Qt
import shutil
import os
import logging
from datetime import datetime
import math
from WaterfallLayout import WaterfallLayout
from ChatPanel import ChatBubble,ChatPanel
root_file=r"C:\Users\xiaobai\Desktop\pet"

current_time = datetime.now().strftime("%Y%m%d")
# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


class GamePanel(QWidget):
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
        self.log_label = QLabel("日记", self)
        #输入框  可换行 滑动
        self.text_edit = QLineEdit(self)
        self.text_edit.setMinimumHeight(100)
        self.setting_list_widget.add_widget(self.log_label)
        self.setting_list_widget.add_widget(self.text_edit)
        self.scroll_area.setWidget(self.setting_list_widget)

        # 使用 QVBoxLayout 来居中 QScrollArea
        self.setting_layout = QVBoxLayout(self)
        self.setting_layout.addWidget(self.scroll_area)

        self.layout.addLayout(self.setting_layout)        
    def show_setting(self,statue_info):
        self.waterfall.clear()
 