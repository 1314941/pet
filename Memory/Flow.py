import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel,QTabWidget,QTextEdit
from PySide6.QtCore import QThread, Signal, Slot,QObject
import time
from datetime import datetime
from decorator import log_task
from LmStudio import action_Model,start_dialog_Model,style_Model,relation_Model,graph_Model



class TaskWorker(QObject):
    finished = Signal()

    def __init__(self, task_function):
        super().__init__()
        self.task_function = task_function

    @Slot()
    def execute(self):
        self.task_function()
        self.finished.emit()



class TaskWidget(QWidget):
    def __init__(self, task_function, prompt_text):
        super().__init__()
        self.task_function = task_function
        self.prompt_text = prompt_text
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.label = QLabel(self.prompt_text)
        self.button_import = QPushButton('导入文件')
        self.button_save = QPushButton('保存')
        self.button_execute = QPushButton('执行任务')
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)  # 设置为只读模式
        layout.addWidget(self.label)
        layout.addWidget(self.button_import)
        layout.addWidget(self.button_save)
        layout.addWidget(self.button_execute)
        layout.addWidget(self.text_edit)
        self.button_import.clicked.connect(self.import_file)
        self.button_save.clicked.connect(self.save_data)
        self.button_execute.clicked.connect(self.start_task)

    def import_file(self):
        # 实现导入文件的功能
        print("导入文件")

    def save_data(self):
        # 实现保存数据的功能
        print("保存数据")



    def start_task(self):
        self.worker = TaskWorker(self.task_function)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.started.connect(self.worker.execute)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()



# 定义一些任务函数
@log_task
def choose_action(message:str):
    model=action_Model()
    model.chat_agent(message)
    #time.sleep(1)  # 模拟耗时操作

@log_task
def relation(message:str):
    model=relation_Model()
    model.chat_agent(message)



@log_task
def graph(message:str):
    model=graph_Model()
    model.chat_agent(message)

@log_task
def style(message:str):
    model=style_Model()
    model.chat_agent(message)

def start_dialog(message:str):
    model=start_dialog_Model()
    model.chat_agent(message)



@log_task

class WorkflowPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('工作流面板')
        self.setGeometry(100, 100, 300, 200)

        # 创建一个QTabWidget来切换不同的任务面板
        self.tab_widget = QTabWidget()

        # 创建任务组件并添加到QTabWidget中  对话  关系提取  图数据库   风格检测  发起对话 
        task1_widget = TaskWidget(start_dialog, "对话")
        task2_widget = TaskWidget(relation, "关系提取")
        self.tab_widget.addTab(task1_widget, "对话")
        self.tab_widget.addTab(task2_widget, "关系提取")
        task_graph_widget = TaskWidget(graph, "图数据库")
        self.tab_widget.addTab(task_graph_widget, "图数据库")
        task_style_widget = TaskWidget(style, "风格检测")
        self.tab_widget.addTab(task_style_widget, "风格检测")
        task_dialog_widget = TaskWidget(start_dialog, "发起对话")
        self.tab_widget.addTab(task_dialog_widget, "发起对话")
        action_widget = TaskWidget(choose_action, "动作")
        self.tab_widget.addTab(action_widget, "动作")

        # 设置QTabWidget作为工作流面板的中央小部件
        self.setCentralWidget(self.tab_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    panel = WorkflowPanel()
    panel.show()
    sys.exit(app.exec())
