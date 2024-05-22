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
import asyncio
import aiohttp


current_time = datetime.now().strftime("%Y%m%d")
# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')




class WaterfallLayout(QWidget):
    def __init__(self,column_count=3):
        super().__init__()

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(10)  # 设置网格间距
        self.grid_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距
        self.items = []  # 存储添加的部件
        self.column_widths = [200,200,200]  # 每列的当前最大宽度
        self.next_row = 0  # 下一个部件将放置的行索引
        self.column_count = 3  # 列数
        self.column_count=column_count
        self.counts=0
    
    def add_widget(self, widget):
        # 计算下一个部件应该放置的列
        column = self.next_column()
        self.grid_layout.addWidget(widget, self.next_row, column)
        self.items.append(widget)
        self.update_column_widths(widget)
        self.next_row=len(self.items)/self.column_count      #一行三个   
        self.counts+=1     

    def next_column(self):
        if self.items==[]:
            return 0;
        # 返回下一个部件应该放置的列
        return len(self.items)%self.column_count

    def update_column_widths(self, widget):
        # 遍历所有列，更新每列的最大宽度
        for i in range(self.column_count):
            self.column_widths[i] = max(self.column_widths[i], widget.sizeHint().width())

    def resizeEvent(self, event):
        # 当窗口大小改变时，重新计算列宽并重新布局
        self.update_column_widths_for_resize()
        super().resizeEvent(event)

    def update_column_widths_for_resize(self):
        # 重新计算每列的宽度
        for widget in self.items:
            self.update_column_widths(widget)

    def item_at(self, index):
        # 根据索引返回对应部件
        return self.items[index]


    def remove_item(self, index):
        # 根据索引移除对应部件
        item = self.items.pop(index)
        self.grid_layout.removeWidget(item)
        item.deleteLater()
        self.update_column_widths_for_resize()

    def clear(self):
        while self.items:
            self.remove_item(0)
            self.update_column_widths_for_resize()


    def count(self):
        return self.counts


