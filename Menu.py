import sys
import random
import ActionPanel
from PySide6.QtCore import Signal,QEvent,QTimer,QObject,QRect,QPoint,QSize
from PySide6.QtWidgets import QWidget,QMenu,QPushButton,QSystemTrayIcon,QLabel,QVBoxLayout,QHBoxLayout,QLineEdit,QFrame
from PySide6.QtGui import QAction,QIcon,Qt
import shutil
import os
import logging
from SettingPanel import SettingPanel
from GamePanel import GamePanel
from datetime import datetime
import math
from WaterfallLayout import WaterfallLayout
from ChatPanel import ChatBubble,ChatPanel
root_file=r"C:\Users\xiaobai\Desktop\pet"

current_time = datetime.now().strftime("%Y%m%d")
# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')



class DesktopPet(QWidget):
    show_clicked=Signal(str)
    close_clicked=Signal(str)
    def __init__(self,parent=None, **kwargs):
        super(DesktopPet,self).__init__(parent)
       
        self.initUI()
        
        self.initPall()

    def initUI(self):
        try:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)  #透明
            self.setStyleSheet("""
                RemiderInterface{
                        background-color: #FFFFFF;
                        border-radius: 10px;
                        border: 1px solid #000000;
                        opacity: 1.0;
                        color: #000000;
                        font-size: 18px;
                        font-weight: 600;
                        font-family: "Microsoft YaHei";
                }
            """)
            # 重绘组件、刷新
            self.repaint()
            #self.hide()
        except Exception as e:
            print("初始化UI出错：", e)

    def show_central(self):
        self.show_clicked.emit("show_central")


     # 托盘化设置初始化
    def initPall(self):
        # 导入准备在托盘化显示上使用的图标
        icons = os.path.join('6.png')
        # 设置右键显示最小化的菜单项
        # 菜单项退出，点击后调用quit函数
        # 菜单项显示，点击后调用showing函数
        showing = QAction(u'显示', self, triggered=self.show_central)
        quit_action = QAction('退出', self, triggered=lambda: self.close_clicked.emit("close_clicked"))
        # 设置这个点击选项的图片
        quit_action.setIcon(QIcon(icons))
        # 新建一个菜单项控件
        self.tray_icon_menu = QMenu(self)
        # 在菜单栏添加一个无子菜单的菜单项‘退出’
        self.tray_icon_menu.addAction(quit_action)
        # 在菜单栏添加一个无子菜单的菜单项‘显示’
        self.tray_icon_menu.addAction(showing)
        # QSystemTrayIcon类为应用程序在系统托盘中提供一个图标
        self.tray_icon = QSystemTrayIcon(self)
        # 设置托盘化图标
        self.tray_icon.setIcon(QIcon(icons))
        # 设置托盘化菜单项
        self.tray_icon.setContextMenu(self.tray_icon_menu)
        # 展示
        self.tray_icon.show()



class MenuButton(QWidget):
    clicked=Signal(str)
    def __init__(self, is_pop=False,text=None,parent=None,widget=None):
        super(MenuButton, self).__init__(parent=None)
        self.initUI(text)
        self.widget=None
        if text is not None:
            self.name.setText(text)
            self.name.adjustSize()
        self.is_pop=is_pop   # 是否弹出
         # 鼠标事件
        self.installEventFilter(self)

        if widget is not None:
            self.widget=widget
            self.widget.installEventFilter(self)
    

    def initUI(self,text):
        if text:
            self.name=QPushButton(text,self)
        else:
            self.name=QPushButton(self)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.name.text())
    
    def setText(self, text):
        self.name.setText(text)
        self.name.adjustSize()

    
    def setAlignment(self):
        self.setAlignment(Qt.AlignCenter)
        self.name.setAlignment(Qt.AlignCenter)




class MenuPanel(QObject):
    def __init__(self, parent=None):
        super(MenuPanel, self).__init__(parent)
        self.initUI()
       
    def initUI(self):
        try:
            #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            #self.setAttribute(Qt.WA_TranslucentBackground)         #透明
            #self.hide()
            #layout = QVBoxLayout(self)
            self.chat_layout=QHBoxLayout()
            self.chat_line=QLineEdit()
            self.chat_line.setPlaceholderText("输入聊天内容")
            self.chat_line.setStyleSheet("background-color: rgba(255, 255, 255, 0.5);")
            self.chat_line.setFixedHeight(30)
            self.send_btn=QPushButton("发送")
            self.send_btn.setStyleSheet("background-color: rgba(255, 255, 255, 0.5);")
            self.send_btn.setFixedHeight(30)
            self.send_btn.clicked.connect(self.send_chat)
            self.chat_layout.addWidget(self.chat_line)
            self.chat_layout.addWidget(self.send_btn)
            self.chat_widget=QWidget()
            self.chat_widget.setLayout(self.chat_layout)
            self.chat_widget.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
            self.chat_widget.hide()
            self.send_btn.clicked.connect(self.resetTimer)
            #当输入框获取焦点时，停止定时器
            self.chat_line.focusInEvent = self.stopTimer
            self.chat_line.focusOutEvent = self.startTimer
            #layout.addLayout(self.chat_layout)

            self.desktop = DesktopPet()       #透明   只是用来添加系统图标
            self.desktop_layout=QHBoxLayout()
            self.desktop_layout.addWidget(self.desktop)
            #layout.addLayout(self.desktop_layout)

            self.talkpanel=TalkPanel(self)
            self.talkpanel.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
            self.talkpanel.hide()
            

            
            #状态面板
            self.setting_panel=SettingPanel()
            self.state_panel = GamePanel()
            self.chat_panel=ChatPanel()

            self.action_window=ActionPanel.ActionWindow()  #动作拼接器

            #出现屏幕中心
            self.chat_panel.setGeometry(QRect(QPoint(512,250),QSize(600,400)))
            #MenuButton   参数设置 text,parent,widget
            self.setting_btn = MenuButton(True,"设置",None,self.setting_panel)   #自动弹出
            self.state_btn = MenuButton(True,"状态",None,self.state_panel)       #绑定状态面板
            self.chat_btn=MenuButton(False,"聊天",None,self.chat_panel)   #不用弹出
            self.action_btn=MenuButton(False,"动作",None,self.action_window)

            self.state_btn.installEventFilter(self)
            self.setting_btn.installEventFilter(self)
            self.setting_panel.installEventFilter(self)
            self.state_panel.installEventFilter(self)

            self.setting_btn.clicked.connect(self.setting_panel.show)
            self.state_btn.clicked.connect(self.state_panel.show) 
            self.chat_btn.clicked.connect(self.chat_panel.show)
            self.action_btn.clicked.connect(self.action_window.show)
            self.setting_btn.clicked.connect(self.resetTimer)
            self.state_btn.clicked.connect(self.resetTimer)
            self.chat_btn.clicked.connect(self.resetTimer)
            self.action_btn.clicked.connect(self.resetTimer)

            button_layout = QHBoxLayout()
            #布局间隔为0  美化
            button_layout.setSpacing(0)
            button_layout.addWidget(self.state_btn)
            button_layout.addWidget(self.action_btn)
            button_layout.addWidget(self.chat_btn)
            button_layout.addWidget(self.setting_btn)
            self.button_widget=QWidget()
            self.button_widget.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
            self.button_widget.setLayout(button_layout)
            self.button_widget.hide()
            #layout.addLayout(button_layout)

            self.timer = QTimer(self.button_widget)
            self.timer.timeout.connect(self.hideWindows)
            self.timer.start(5000)  # 5000毫秒后触发超时
        except Exception as  e:
            print(e)
            logging.error(e)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            if obj == self.setting_btn and self.setting_btn.is_pop:   #弹出标志
                self.setting_panel.setVisible(True)
            elif obj == self.setting_panel:
                # 鼠标进入面板时，不隐藏面板
                pass
            if obj==self.state_btn and self.state_btn.is_pop:
                self.setting_panel.setVisible(True)
            elif obj == self.setting_panel:
                # 鼠标进入面板时，不隐藏面板
                pass
        elif event.type() == QEvent.Leave:
            if obj == self.setting_btn:
                # 鼠标离开按钮时，不隐藏面板（如果鼠标在面板上）
                if not self.state_panel.underMouse():
                    self.state_panel.setVisible(False)
            elif obj == self.state_panel:
                # 鼠标离开面板时，隐藏面板
                self.state_panel.setVisible(False)
            if obj == self.state_btn:
                # 鼠标离开按钮时，不隐藏面板（如果鼠标在面板上）
                if not self.state_panel.underMouse():
                    self.state_panel.setVisible(False)
            elif obj == self.state_panel:
                # 鼠标离开面板时，隐藏面板
                self.state_btn_panel.setVisible(False)
        return super().eventFilter(obj, event)

    def send_chat(self):
        chat_text=self.chat_line.text()
        if chat_text:
            self.send_btn.setEnabled(False)
            self.send_btn.setText("发送中...")

    def show(self):
        self.chat_widget.show()
        self.button_widget.show()


    def move_menu(self,horizontal,vertical,width,height):
        #self.move(horizontal,vertical)
        #self.resize(width,height)
        self.chat_widget.setGeometry(horizontal,vertical-height/8,width,30)
        self.button_widget.setGeometry(horizontal,vertical+height/2+150,width,50)
        #设置面板一直出现在按钮面板正上方
        self.panel_width=width
        self.panel_height=height/2
        self.panel_x=horizontal
        self.panel_y=vertical+height/2+150-self.panel_height  #10为按钮面板的上部分高度
        self.setting_panel.setGeometry(self.panel_x,self.panel_y,self.panel_width,self.panel_height)
        self.state_panel.setGeometry(self.panel_x,self.panel_y,self.panel_width,self.panel_height)
        self.talkpanel.setGeometry(self.panel_x,self.panel_y,self.panel_width,self.panel_height)

    def anyWindowUnderMouse(self):
        """检查是否有窗口在鼠标下方"""
        widgets = [self.chat_widget, self.button_widget, self.setting_panel, self.state_panel, self.talkpanel]
        for widget in widgets:
            if widget.isVisible() and widget.underMouse():
                return True
        return False


    def hideWindows(self):
        """隐藏所有窗口的方法"""
        if not self.anyWindowUnderMouse():
            if self.chat_widget.isVisible():
                self.chat_widget.hide()
            if self.button_widget.isVisible():
                self.button_widget.hide()
            if self.setting_panel.isVisible():
                self.setting_panel.hide()
            if self.state_panel.isVisible():
                self.state_panel.hide()
            if self.talkpanel.isVisible():
                self.talkpanel.hide()
        else:
            self.resetTimer()


    def startTimer(self,event):
        self.timer.start(5000)  # 启动计时器

    def stopTimer(self,event):
        self.timer.stop()

    def resetTimer(self,text=None):
        self.timer.start(5000)  # 重置计时器




class TalkLabel(QWidget):
    def __init__(self, text=None,parent=None):
        super().__init__(parent=None)
        if parent:
            self.parent=parent
        self.initUI()
        if text:
            self.setText(text)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.hide()
        self.name = QLabel(self)
    
    def setText(self,text):
        if not text:
            return
        self.name.setText(text)
        self.name.adjustSize()

    def setAlignment(self):
        self.setAlignment(Qt.AlignCenter)
        self.name.setAlignment(Qt.AlignCenter)


class TalkPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=None)
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.hide()
        layout = QVBoxLayout(self)
        self.talk_label=TalkLabel(None,self)
        self.talk_label.setStyleSheet("background-color: rgba(255,255,255,0.5);")
        layout.addWidget(self.talk_label,0,Qt.AlignCenter)

    def setText(self, text):
        self.talk_label.setText(text)
        self.talk_label.adjustSize()
