from chat_database import create_db,init_user,add_chat
create_db()
import basic_database
basic_database.init_db()
import threading
import sys
import random
from PySide6.QtCore import QPoint,QTimer,Signal,Slot
from PySide6.QtWidgets import QWidget,QApplication,QLabel
from PySide6.QtGui import QCursor,QPixmap
import shutil
import os
import math
import Port
from Menu import MenuPanel,TalkPanel
from PySide6.QtCore import Qt,QThread   
from MoodWorker import MoodWorker
from datetime import datetime
import logging
root_file=r"C:\Users\xiaobai\Desktop\pet"

current_time = datetime.now().strftime("%Y%m%d")
# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')



class Pet(QLabel):
    #动作开始信号
    action_started_signal = Signal(str)
    #动作完成信号
    action_finished_signal = Signal(str)
    def __init__(self, width,height,parent=None):
        super().__init__(parent)
        try:
            Port.start()
            basic_database.load_gpt_sovits_params()
            basic_database.load_port_settings()
            self.screen_width=width
            self.screen_height=height
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint|Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground,True)   #好无语啊  为啥有时候显示不了 关闭再来一次又可以
            self.setMouseTracking(True)

            self.menu = MenuPanel(self)
            #self.menu.hideWindow()
            self.menu.desktop.show_clicked.connect(self.show_central)
            self.menu.desktop.close_clicked.connect(self.close_event)
            self.action_window=self.menu.action_window
            self.is_quiet = False  # 安静模式标志
            self.is_follow_mouse=False
            self.start_thread()
            self.initPetImage()
            self.petNormalAction()
        except Exception as e:
            logging.error(f"初始化桌面宠物时发生错误：{e}")
            print("初始化桌面宠物时发生错误：",e)

    def start_thread(self):
        self.thread = QThread()
        self.moodWorker = MoodWorker(self.action_window)
        self.moodWorker.chatdialog=self.menu.talkpanel         # 绑定聊天对话框  
        self.moodWorker.show_action_signal.connect(self.show_action, Qt.ConnectionType.QueuedConnection)
        self.moodWorker.moveToThread(self.thread)
        self.thread.started.connect(self.moodWorker.moodtimer.start)
        self.thread.start()
        self.moodWorker.interact_signal.connect(self.start_interaction)
        #为了确保 updateAnimation 在主线程中被执行，您可以使用 QMetaObject.invokeMethod 来在主线程中安全地调用它，或者您可以在连接信号时显式指定 Qt.ConnectionType.QueuedConnection
        #失败  无法启动函数
        #self.moodWorker.show_next_action_signal.connect(self.updateAnimation, Qt.ConnectionType.QueuedConnection)
     


    @Slot(str)
    def show_central(self,text):
        self.move(512,400)

        
     # 宠物随机位置出现
    def randomPosition(self):
        # 获取窗口坐标系
        pet_geo = self.geometry()
        width = (self.screen_width - pet_geo.width()) * random.random()
        height = (self.screen_height - pet_geo.height()) * random.random()
        self.pet_pos=QPoint(random.randint(0,self.screen_width/2),random.randint(0,self.screen_height/2))
        self.setGeometry(self.pet_pos.x(),self.pet_pos.y(),100,100)
    


    def initPetImage(self):
        self.image_index = 0
        self.mode="move"
        # 设置宠物的速度
        self.speed = 10  # 假设宠物的速度是10像素/步
        self.interacting = False  # 互动模式标志
        self.end_signal=False  #唯一的辉煌！
        self.action=None
        self.rest_probability=0.25  # 0.05的概率进行休息
        self.interaction_changed=False
        self.current_direction=None
        self.interaction_lock= threading.Lock()  # 创建一个互斥锁
        self.menu_width=1.05      #菜单出现在桌宠的右上角距离比例
        self.menu_height=1.2
     
        # 调用自定义的randomPosition，会使得宠物出现位置随机
        self.randomPosition()
        self.show()


    def movePet(self):
        if self.mode == "move":
            # 有一定的概率不进行移动，而是执行其他动作
            if random.randint(1, 100) > 95:  # 5%的概率执行其他动作
                # 这里可以添加其他动作的代码
                return
          
        current_x = self.x()
        current_y = self.y()
        screen_width = self.screen_width
        screen_height = self.screen_height

        # Decide if the pet should rest or move
        if random.random() < self.rest_probability or self.current_direction is None:
            self.current_direction = None  # Rest, no direction
        else:
            # Continue moving in the current direction or choose a new one
            if self.current_direction is None:
                self.current_direction = random.choice(['left', 'right', 'up', 'down'])

        # Determine the new position based on the current direction
        if self.current_direction == 'left':
            new_x = max(0, current_x - self.move_distance)
            new_y = current_y
        elif self.current_direction == 'right':
            new_x = min(screen_width - self.width(), current_x + self.move_distance)
            new_y = current_y
        elif self.current_direction == 'up':
            new_x = current_x
            new_y = max(0, current_y - self.move_distance)
        elif self.current_direction == 'down':
            new_x = current_x
            new_y = min(screen_height - self.height(), current_y + self.move_distance)
        else:
            new_x, new_y = current_x, current_y


        # 更新宠物的位置
        new_pos = QPoint(new_x, new_y)
      
        self.pet_pos = new_pos
        self.move(self.pet_pos)
        self.update()
        #水平中心点
        horizontal_center = self.geometry().x()
        #垂直中心点
        vertical_center = self.geometry().y()
        #菜单长宽
        menu_width = self.width()*self.menu_width
        menu_height = self.height()*self.menu_height
        self.menu.move_menu(horizontal_center,vertical_center,menu_width,menu_height)
                

    def deleteFile(self):
        # 删除拖放到桌宠上的文件
        print("删除文件")
   
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
   

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            os.remove(file_path)  # 删除文件
            print(f"文件已删除: {file_path}")

    # 鼠标移进时调用
    def enterEvent(self, event):
        # 设置鼠标形状 Qt.ClosedHandCursor   非指向手
        self.setCursor(Qt.ClosedHandCursor)

     # 鼠标左键按下时, 宠物将和鼠标位置绑定
    def mousePressEvent(self, event):
        globalPos = QCursor.pos()   # globalPos() 事件触发点相对于桌面的位置
        #转为点击状态
        if event.button() == Qt.LeftButton:
            self.is_follow_mouse = True
            # pos() 程序相对于桌面左上角的位置，实际是窗口的左上角坐标
            self.mouse_drag_pos = globalPos - self.pos()
            event.accept()
            # 拖动时鼠标图形的设置
            self.setCursor(QCursor(Qt.OpenHandCursor))
        elif event.button() == Qt.RightButton:        #右键面板
            self.menu.show()
 
    # 鼠标移动时调用，实现宠物随鼠标移动
    def mouseMoveEvent(self, event):
        # 如果鼠标左键按下，且处于绑定状态
        if Qt.LeftButton and self.is_follow_mouse:
            # 宠物随鼠标进行移动
            self.moodWorker.interact_action=self.moodWorker.interact_actions['lift']  #飘起来
            self.start_interaction()
            globalPos = QCursor.pos();
            self.pet_pos=globalPos - self.mouse_drag_pos
            self.move(globalPos - self.mouse_drag_pos)
        event.accept()


    # 鼠标释放调用，取消绑定
    def mouseReleaseEvent(self, event):
        self.end_interaction()
        self.is_follow_mouse = False
        # 鼠标图形设置为箭头
        self.setCursor(QCursor(Qt.ArrowCursor))

    def start_interaction(self):
        with self.interaction_lock:
            # 确保只被调用一次
            if self.moodWorker.interact_action is None:
                return
            if not self.interacting:
                # 当开始交互时调用这个方法
                self.origin_image_index=self.image_index
                self.action = self.moodWorker.interact_action  # 交互动作
                self.interacting = True
                self.image_index = 0  # 重置索引


    def end_interaction(self):
        with self.interaction_lock:
            if self.interacting:
                # 当交互结束时调用这个方法
                self.interacting = False
                self.interaction_changed=True
    
    
    @Slot(bool)
    def updateAnimation(self):
        try:
            if self.interaction_changed:
                if self.image_index>=len(self.action):
                    self.image_index=self.origin_image_index
                    self.interaction_changed=False
            else:
                if self.interacting:
                    # 如果正在交互，则继续执行交互动作
                    print("interacting")
                    self.image_index += 1
                    try:
                        if self.image_index >= len(self.action):
                            if self.end_signal==True:  #一切都节俗辣
                                self.close()
                            print("interactiong_actions",self.action)
                            self.image_index=0
                            self.end_interaction()
                    except Exception as e:
                        print("error:",e)
                        self.end_interaction()
                else:
                    self.action=self.moodWorker.nomal_actions
                    if self.image_index >= len(self.action):
                        print("image_index:",self.image_index)
                        #print("len(action):",len(self.action))
                        self.image_index = 0
            pixmap_path=self.action[self.image_index]
            #print('pixmap_path:'+pixmap_path)
            pixmap=QPixmap(pixmap_path)
            self.setPixmap(pixmap)
            self.setFixedSize(pixmap.width()/2.5, pixmap.height()/2.5)
            self.setScaledContents(True)
            self.repaint()
            self.update()
            self.show()
            self.image_index += 1
        except Exception as e:
            print(e)

    def petNormalAction(self):
        # 设置定时器来移动桌宠  
        self.timer = QTimer(self) 
        self.timer.timeout.connect(self.movePet)
        self.timer.start(200) 
        print("开始移动桌宠")

         # 设置定时器来移动桌宠  
        self.moodWorker.interact_action=self.moodWorker.interact_actions['start']
        self.start_interaction()
        self.action=self.moodWorker.nomal_actions
        self.updatetimer = QTimer(self) 
        self.updatetimer.timeout.connect(self.updateAnimation)
        self.updatetimer.start(200) 
        print("开始移动桌宠")
   
    @Slot(str)
    def show_action(self,signal):
       pass

    def show_close_action(self):
        self.moodWorker.interact_action=self.moodWorker.interact_actions['end']
        self.end_signal=True
        self.start_interaction()

    def close_event(self):
        self.show_close_action()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    #获取屏幕大小
    screen_size = app.primaryScreen().size()
    width = screen_size.width()
    height = screen_size.height()
    pet=Pet(width,height)
    app.exec()



'''  #旧的提取文本函数
    def read_dialogues(self,file_path):
        #替换字符
        file_path=os.path.normpath(file_path)
        # 指定目标文件夹路径
        target_folder = 'text'

        # 确保目标文件夹存在
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        # 复制文件到目标文件夹
        # 获取文件名
        file_name = os.path.basename(file_path)

        # 获取文件名和扩展名的部分
        base_name,extension = os.path.splitext(file_name)
        destination_path = os.path.join(target_folder,f'{base_name}.txt')

        if not os.path.exists(destination_path):
            # 复制文件并重命名
            shutil.copy2(file_path, destination_path)
            os.rename(file_path, destination_path)

        try:
            with open(destination_path, 'r', encoding='utf-8') as file:
                lines = file.read()
        except FileNotFoundError:
            print(f"The file {destination_path} was not found.")
        except IOError:
            print(f"An error occurred while trying to read the file {destination_path}.")
        self.dialogues = []

        for line in lines:
            # 假设每行文本都是独立的对话
            parts = line.strip().split(':|')
            dialogue_data = {}
            for i,part in enumerate(parts):
                if i == 0:
                    pass
                else:
                    # 解析键值对
                    key, value = part.split('#', 1)
                    dialogue_data[key] = value
                    # 添加到对话列表
            self.dialogues.append(dialogue_data)
        return self.dialogues


'''