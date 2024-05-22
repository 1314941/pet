import os
import json
import sqlite3
from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget,QLabel,QHBoxLayout,QPushButton,QMenu,QAbstractItemView,QTabWidget,QFileDialog
from PySide6.QtCore import QDir, QModelIndex, Qt, Signal,QTimer,QSize
from PySide6.QtGui import QStandardItem, QStandardItemModel,QPixmap,QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLabel,QListWidgetItem,QLineEdit,QTableWidget,QTableWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor,QIntValidator



class FileTreeModel(QStandardItemModel):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_item = self.invisibleRootItem()

    def add_file(self, file_path):
        # 将文件路径分割成目录和文件名
        path_list = file_path.split(os.sep)
        # 从根目录开始，逐级添加目录和文件
        parent_item = self.root_item
        for folder_name in path_list[:-1]:
            # 查找或创建子目录项
            found = False
            for i in range(parent_item.rowCount()):
                child_item = parent_item.child(i)
                if child_item.text() == folder_name:
                    parent_item = child_item
                    found = True
                    break
            if not found:
                child_item = QStandardItem(folder_name)
                child_item.setEditable(False)
                #将文件路径存储在UserRole中
                folder_path = os.path.normpath(file_path)
                folder_path=os.path.dirname(folder_path)
                child_item.setData(folder_path, Qt.UserRole)
                parent_item.appendRow(child_item)
                parent_item = child_item

        # 添加文件项
        file_item = QStandardItem(path_list[-1])
        file_item.setEditable(False)
        parent_item.appendRow(file_item)
        if file_item.text().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            file_item.setData(file_path, Qt.UserRole)

    def scan_folder(self, folder_path):
        if not os.path.exists(folder_path):
            print(f"文件夹 {folder_path} 不存在")
            return
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                self.add_file(file_path)
    
    def get_image_files(self, folder_path):
        image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        return image_files



class PreviewPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_folder_path = None
        #播放速度
        self.speed=None    #令人无语的bug
        self.speed = 200
        self.image_files = []  # 存储文件夹内的图像文件路径
        self.current_image_index = -1  # 当前显示的图像索引
        self.paused = True  # 暂停标志
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_next_image)
        self.initUI()

    def initUI(self):
        self.preview_label = QLabel(self)
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setAlignment(Qt.AlignCenter)

        self.next_button = QPushButton("下一个", self)
        self.prev_button = QPushButton("上一个", self)
        self.pause_button = QPushButton("暂停/播放", self)
        #播放速度
        self.speed_label = QLabel("播放速度(毫秒):", self)
        self.speed_input = QLineEdit(self)
        self.speed_input.setText(str(self.speed))
        self.speed_input.editingFinished.connect(self.on_speed_input_enter)
        self.speed_input.setFixedWidth(100)
        self.speed_input.setValidator(QIntValidator(1, 10000, self))
        self.next_button.clicked.connect(self.show_next_image)
        self.prev_button.clicked.connect(self.show_prev_image)
        self.pause_button.clicked.connect(self.toggle_pause)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.speed_label)
        button_layout.addWidget(self.speed_input)

        show_layout=QVBoxLayout()
        show_layout.addWidget(self.preview_label)
        show_layout.addLayout(button_layout)

        layout = QVBoxLayout()
        layout.addLayout(show_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    
    
    def update_speed(self, new_speed):
        self.speed = int(new_speed)
        self.speed_input.setText(str(self.speed))
        if self.timer:
            self.timer.stop()
            self.timer.start(int(self.speed))



    def on_speed_input_enter(self):
        # 当用户在 speed_input 中输入文本并按下 Enter 键时，这个函数会被调用
        # 你可以在这里处理速度值
        speed_value = self.speed_input.text()
        print(f"输入的速度值是: {speed_value}")
        self.update_speed(speed_value)

    def show_image(self, file_path):
        pixmap = QPixmap(file_path)
        self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def show_next_image(self):
        if self.image_files:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.show_image(self.image_files[self.current_image_index])

    def show_prev_image(self):
        if self.image_files:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
            self.show_image(self.image_files[self.current_image_index])

    def toggle_pause(self):
        self.paused = not self.paused
        if not self.paused and self.timer:
            self.timer.start(self.speed)
        if self.paused and self.timer:
            self.timer.stop()

    def start_auto_play(self):
        if self.timer:
            self.timer.stop()
        self.timer.start(self.speed)  # 2000毫秒切换一次图像




class ActionFilePanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.action_file='mod/pet/vup'
        self.files=[]
        self.setWindowFlags(Qt.WindowStaysOnTopHint|Qt.FramelessWindowHint)
        self.initUI()
        
    def initUI(self):
        self.open_btn=QPushButton('打开文件夹',self)
        self.open_btn.clicked.connect(self.open_file_dialog)
        self.pre_panel=PreviewPanel()
        self.tree_view = QTreeView(self)
        self.tree_view.clicked.connect(self.on_item_clicked)
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.open_btn)
        layout.addWidget(self.tree_view)
        layout.addWidget(self.pre_panel)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.model = FileTreeModel(self)
        self.tree_view.setModel(self.model)
        self.model.scan_folder(self.action_file)  # 替换为你的文件夹路径

    def open_file_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            self.model.scan_folder(folder_path)
            self.files.append(folder_path)

    def load_file(self):
        for folder_path in self.files:
            self.model.scan_folder(folder_path)

    def on_item_clicked(self, index: QModelIndex):
        item = self.model.itemFromIndex(index)
        if item.hasChildren():
            folder_path = item.data(Qt.UserRole)
            if folder_path:
                self.pre_panel.image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
                if self.pre_panel.image_files:
                    self.pre_panel.current_folder_path = folder_path
                    self.pre_panel.current_image_index = 0
                    self.pre_panel.show_image(self.pre_panel.image_files[self.pre_panel.current_image_index])
                    self.pre_panel.start_auto_play()
        else:
            file_path = item.data(Qt.UserRole)
            if file_path and file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                pixmap = QPixmap(file_path)
                self.pre_panel.preview_label.setPixmap(pixmap.scaled(self.pre_panel.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_item_double_clicked(self, index: QModelIndex):
        item = self.model.itemFromIndex(index)
        if item.hasChildren():
            folder_path = item.data(Qt.UserRole)
            if folder_path:
                self.pre_panel.image_files = self.model.get_image_files(folder_path)
                if self.pre_panel.image_files:
                    self.pre_panel.current_image_index = 0
                    self.pre_panel.show_image(self.pre_panel.image_files[self.pre_panel.current_image_index])
                    self.pre_panel.start_auto_play()

    def get_to_add(self):
        return self.pre_panel.current_folder_path,self.pre_panel.image_files  #当前播放图像列表

   

class ActionComponent(QWidget):
    def __init__(self, action_name,image_files):
        super().__init__()
        self.image_files = image_files  #该动作的图像列表

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(action_name)
        self.layout.addWidget(self.label)


#组合窗口
class NomalPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        print("初始化组合窗口")
        self.initUI()

    def initUI(self):
        try:
            self.list_widget = QListWidget(self)
            self.list_widget.setViewMode(QListWidget.ListMode)
            self.list_widget.setWordWrap(True)
             # 设置拖动和排序模式
            self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
            self.list_widget.setSelectionMode(QListWidget.SingleSelection)
            self.list_widget.itemSelectionChanged.connect(self.selection_changed)
            #右键菜单
            self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
            
            self.pre_panel=PreviewPanel()

            layout = QVBoxLayout()
            layout.addWidget(self.list_widget)
            layout.addWidget(self.pre_panel)

            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)
        except Exception as  e:
            print("初始化组合窗口失败",e)

    def add_action(self,folder_path,image_files):
        #添加进列表
        action_name = folder_path

          # 获取当前选中的项的索引
        current_row = self.list_widget.currentRow()

        item = QListWidgetItem(self.list_widget)
        item.setText(action_name)
        item.setData(Qt.UserRole, image_files)  # 存储 image_files 列表作为数据
        # 如果当前没有选中的项，或者当前选中的项是列表的最后一个，则添加到列表的末尾
        if current_row == -1 or current_row == self.list_widget.count() - 1:
            self.list_widget.addItem(item)
        else:
            # 否则，在当前选中的项之后添加新项
            self.list_widget.insertItem(current_row + 1, item)
        self.previous_item = item

        #new_image_files=[]
        #for i in range(self.list_widget.count()):
        for image_file in image_files:
            self.pre_panel.image_files.append(image_file)
        self.pre_panel.start_auto_play()

    def selection_changed(self):
        # 恢复上一个选中项的颜色
        if self.previous_item:
            self.previous_item.setBackground(QColor(255, 255, 255))

        # 获取当前选中项
        current_items = self.list_widget.selectedItems()
        if current_items:
            current_item = current_items[0]
            # 设置当前选中项的颜色
            current_item.setBackground(QColor(200, 200, 255))
            # 保存当前选中项作为上一个选中项
            self.previous_item = current_item

    def show_context_menu(self, pos):
        # 创建菜单
        menu = QMenu(self)
        # 添加菜单项
        # 例如，你可以添加一个用于删除当前选中项的菜单项
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self.delete_selected_item)
        menu.addAction(delete_action)

        # 显示菜单
        menu.popup(self.list_widget.mapToGlobal(pos))

    def delete_selected_item(self):
        #删除
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            self.list_widget.takeItem(self.list_widget.row(item))
             # 获取关联的 image_files 列表
            image_files = item.data(Qt.UserRole)
            # 去除 image_files 中的对应图像路径
            for image_file in image_files:
                self.pre_panel.image_files.remove(image_file)

    def get_nomal_actions(self):
        return self.pre_panel.image_files


class CustomTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, image_files=None):
        super().__init__(text)
        self.setSizeHint(QSize(100, 20))  # 设置一个固定的大小
        self.image_files = image_files  # 存储 image_files 列表

    def get_image_files(self):
        return self.image_files
    
    def set_image_files(self, image_files):
        self.image_files = image_files

    def clone(self):
        # 创建一个新的 CustomTableWidgetItem 对象，并复制 image_files 列表
        clone = CustomTableWidgetItem(self.text(), self.image_files[:])
        return clone


class Interact_Panel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint|Qt.FramelessWindowHint)
        self.current_item = None
        self.current_action=None
        self.initUI()

    def initUI(self):
          # 创建 QTableWidget
        self.tableWidget = QTableWidget()

        # 设置表格的行数和列数
        self.tableWidget.setRowCount(7)  # 可以根据需要调整行数
        self.tableWidget.setColumnCount(2)  # 左边一列是动作名称，右边一列是动作动作名称

        # 添加表格头
        self.tableWidget.setHorizontalHeaderLabels(["动作名称", "动作"])

        # 添加表格数据
        self.tableWidget.setItem(0, 0, QTableWidgetItem("eat"))
        self.tableWidget.setItem(0, 1,CustomTableWidgetItem("吃"))
        self.tableWidget.setItem(1, 0, QTableWidgetItem("lift"))
        self.tableWidget.setItem(1, 1, CustomTableWidgetItem("抬"))
        self.tableWidget.setItem(2, 0, QTableWidgetItem("pat"))
        self.tableWidget.setItem(2, 1, CustomTableWidgetItem("摸头"))
        self.tableWidget.setItem(3, 0, QTableWidgetItem("drink"))
        self.tableWidget.setItem(3, 1, CustomTableWidgetItem("喝"))
        self.tableWidget.setItem(4, 0, QTableWidgetItem("say"))
        self.tableWidget.setItem(4, 1,CustomTableWidgetItem("说"))
        self.tableWidget.setItem(5, 0, QTableWidgetItem("start"))
        self.tableWidget.setItem(5, 1, CustomTableWidgetItem("开始"))
        self.tableWidget.setItem(6, 0, QTableWidgetItem("end"))
        self.tableWidget.setItem(6, 1, CustomTableWidgetItem("结束"))


        self.tableWidget.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableWidget.setSelectionMode(QTableWidget.SingleSelection)

        self.pre_panel=PreviewPanel()

        layout = QVBoxLayout()
        layout.addWidget(self.tableWidget)
        layout.addWidget(self.pre_panel)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def find_matching_actions(self, text):
        # 使用 findItems 方法查找与输入内容匹配的 QTableWidgetItem
        items = self.tableWidget.findItems(text, Qt.MatchExactly)
        if items:
            row=items[0].row()
            find_action = self.tableWidget.item(row, 1).get_image_files()
            # 如果找到匹配的项目，返回第一个项目
            return find_action
        return None
    

    def on_item_selection_changed(self):
            # 当用户选择一个新项目时，更新当前动作
            selected_items = self.tableWidget.selectedItems()
            self.current_item=selected_items
            if selected_items:
                row = selected_items[0].row()
                column = selected_items[0].column()
                current_action = self.tableWidget.item(row, column).text()
                self.pre_panel.image_files=self.tableWidget.item(row,1).get_image_files()
                self.pre_panel.start_auto_play()
                self.current_action = current_action
                print(f"当前选中的动作是: {current_action}")

    def update_action(self,folder_path,image_files):
        if self.current_item==None:
            print("请先选择一个动作")
            return 
        row = self.current_item[0].row()
        if self.current_item[0].column()==0:
            print("选中了第一列，默认选错，修改第二列数据")
        self.tableWidget.setItem(row, 1, CustomTableWidgetItem(folder_path,image_files))
        self.pre_panel.image_files=image_files
        self.pre_panel.start_auto_play()
        
    def load_action_from_db(self,row,folder_path,image_files=None):
        self.tableWidget.setItem(row, 1, CustomTableWidgetItem(folder_path,image_files=image_files))
        self.pre_panel.image_files=image_files

            


class ActionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = 'database/action.db'  # 数据库文件路径
        self.init_database()
        self.setWindowTitle("动作组合器")
        db_dir=os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.initUI()
        self.load_action()  #加载配置

    def initUI(self):
        try:
            # 创建 QTabWidget
            self.right_tabWidget = QTabWidget()

            self.interact_panel=Interact_Panel()
            self.update_btn=QPushButton("更新")
            self.update_btn.clicked.connect(self.update_interact_action)
            self.interact_window=QWidget()
            self.interact_window.setLayout(QHBoxLayout())
            self.interact_window.layout().addWidget(self.update_btn)
            self.interact_window.layout().addWidget(self.interact_panel)
          
            self.right_panel = None
            self.right_panel = NomalPanel()
            #中间按钮集合
            self.add_button=QPushButton("添加")
            self.add_button.clicked.connect(self.add_action)
            self.delete_button=QPushButton("删除")
            self.delete_button.clicked.connect(self.delete_action)
            self.middle_layout=QVBoxLayout()
            self.middle_layout.addWidget(self.add_button)
            self.middle_layout.addWidget(self.delete_button)
            #间隔为0
            self.middle_layout.setSpacing(0)
            self.left_panel=ActionFilePanel()
            layout = QHBoxLayout()
            layout.addWidget(self.left_panel)

            self.nomal_panel=QWidget()
            self.nomal_panel.setLayout(QHBoxLayout())
            self.nomal_panel.layout().addLayout(self.middle_layout)
            self.nomal_panel.layout().addWidget(self.right_panel)

            self.right_tabWidget.addTab(self.nomal_panel, "日常")
            self.right_tabWidget.addTab(self.interact_window, "互动")
            layout.addWidget(self.right_tabWidget)
            self.setLayout(layout)
        except Exception as e:
            print("初始化失败", e)
    
    def add_action(self):
        folder_path,image_files=self.left_panel.get_to_add()
        self.right_panel.add_action(folder_path,image_files)


    def delete_action(self):
        self.right_panel.delete_selected_item()

    def update_interact_action(self):
        folder_path,image_files=self.left_panel.get_to_add()
        self.interact_panel.update_action(folder_path,image_files)
        pass

    def closeEvent(self, event):
        # 在关闭事件中保存数据
        self.save_action()
        # 允许关闭事件继续执行
        event.ignore()
        self.hide()

    def init_database(self):
         # 保存动作数据到文件
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建表（如果表不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nomal_actions (
                    id INTEGER PRIMARY KEY,
                    folder_path TEXT,
                    image_files JSON
                )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS interact_actions (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                folder_path TEXT,
                actions JSON
            )
        ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_setting(
                    id INTERGER PRIMARY KEY,
                    left_speed INT,
                    right_speed INT,
                    action_files JSON
                )
            ''')
            conn.commit()
            cursor.close()
            conn.close()

    def save_action(self):
        try:
             # 保存动作数据到文件
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取当前选中的项的索引
            current_row = self.right_panel.list_widget.currentRow()

            
                
            # 清空数据库  重新写入
            cursor.execute('DELETE FROM nomal_actions')


            # 遍历 QListWidget 中的所有项
            for row in range(self.right_panel.list_widget.count()):
                item = self.right_panel.list_widget.item(row)

                image_files = item.data(Qt.UserRole)  # 获取关联的 image_files 列表
                # 保存数据到数据库
                cursor.execute('''
                    INSERT INTO nomal_actions (folder_path, image_files)
                    VALUES (?, ?)
                ''', (item.text(),json.dumps(image_files)))

                # 获取速度值
            left_speed = int(self.left_panel.pre_panel.speed)
            right_speed = int(self.left_panel.pre_panel.speed)

            # 检查是否存在记录
            cursor.execute('''
                SELECT COUNT(*) FROM action_setting
            ''')
            count = cursor.fetchone()[0]

            # 如果存在记录，则更新
            if count > 0:
                cursor.execute('''
                    UPDATE action_setting
                    SET left_speed = ?, right_speed = ?
                ''', (left_speed, right_speed))
            else:
                # 如果不存在记录，则插入
                cursor.execute('''
                    INSERT INTO action_setting (left_speed, right_speed)
                    VALUES (?, ?)
                ''', (left_speed, right_speed))

            # 检查是否存在记录
            cursor.execute('''
                SELECT COUNT(*) FROM interact_actions
            ''')
            count = cursor.fetchone()[0]
        
            # 遍历表格中的所有项目
            for row in range(self.interact_panel.tableWidget.rowCount()):
                name_item=self.interact_panel.tableWidget.item(row, 0)
                name=name_item.text()
                action_item = self.interact_panel.tableWidget.item(row, 1)
                folder_path = action_item.text()
                action = action_item.get_image_files()
                action=json.dumps(action)
                if count>0:
                        cursor.execute('''
                        UPDATE interact_actions
                        SET  actions = ? WHERE  folder_path = ?
                    ''', (action,folder_path))
                else:
                    cursor.execute('''
                        INSERT INTO interact_actions (name,folder_path, actions)
                        VALUES (?, ?,?)
                    ''', (name,folder_path, action))

            # 提交事务并关闭连接
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(e)

    def load_action(self):
        print("加载配置")
        # 从文件中加载动作数据
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 从数据库表中加载数据
        cursor.execute('SELECT * FROM nomal_actions')
        rows = cursor.fetchall()
        if rows:
            # 清除 QListWidget 中的所有项
            self.right_panel.list_widget.clear()

            # 遍历加载的数据并添加到 QListWidget  获取日常图像文件路径
            for row in rows:
                id,folder_path, image_files_json = row
                # 将 JSON 字符串转换为 Python 对象
                image_files = json.loads(image_files_json)
                self.right_panel.add_action(folder_path, image_files)
            
        #获取配置  播放速度
        cursor.execute('SELECT * FROM action_setting')
        rows = cursor.fetchall()
        if len(rows)>0:
            id,left_speed,right_speed,files = rows[0]
            self.left_panel.pre_panel.speed = left_speed
            self.left_panel.pre_panel.speed = right_speed
            self.left_panel.pre_panel.update_speed(left_speed)
            self.right_panel.pre_panel.update_speed(right_speed)
            if files:
                self.left_panel.files=json.loads(files)
            self.left_panel.load_file()  #加载

        cursor.execute('SELECT * FROM interact_actions')
        rows=cursor.fetchall()
        if rows:
            for i, row in enumerate(rows):
                id,name,folder_path,image_files_json = row
                image_files = json.loads(image_files_json)
                self.interact_panel.load_action_from_db(i,folder_path,image_files)
        # 提交事务并关闭连接
        conn.commit()
        conn.close()

        pass



'''
app = QApplication([])

main_window = ActionWindow()
main_window.show()

app.exec()
'''