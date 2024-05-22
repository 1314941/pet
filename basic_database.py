import sqlite3
import Port
import tts

# 数据库文件的路径
db_path = 'basic.db'



def init_db():
    # 创建或连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建一个表来保存参数
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gpt_sovits_params (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL DEFAULT 'ollama' UNIQUE,
        url TEXT,
        refer_wav_path TEXT,
        prompt_text TEXT,
        prompt_language TEXT,
        text TEXT,
        text_language TEXT
    )
    ''')

      # 创建一个表来保存接口设置
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS port_settings (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL DEFAULT 'one' UNIQUE,
        ollama_port INTEGER,
        ollama_command TEXT,
        gpt_sovits_port INTEGER,
        gpt_sovits_path TEXT,
        sovits_weights TEXT,
        gpt_weights TEXT,
        gpt_sovits_text TEXT,
        gpt_sovits_voice TEXT,
        gpt_sovits_language TEXT,
        gpt_sovits_command TEXT
    )
    ''')

    conn.commit()
    cursor.close()
    conn.close()

def add_gpt_sovits_params(name,url, refer_wav_path, prompt_text, prompt_language, text, text_language):
     # 创建或连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
       #根据设置名称查询是否存在
    cursor.execute('SELECT * FROM gpt_sovits_params WHERE name=?', (name,))
    result = cursor.fetchone()
    #如果存在，结束
    if result:
        return
    # 插入数据
    cursor.execute('''
    INSERT INTO gpt_sovits_params (name,url, refer_wav_path, prompt_text, prompt_language, text, text_language)
    VALUES (?,?, ?, ?, ?, ?, ?)
    ''', (name,url, refer_wav_path, prompt_text, prompt_language, text, text_language))

    # 提交事务
    conn.commit()

    # 关闭连接
    cursor.close()
    conn.close()

#更新
def update_gpt_sovits_params(name,url, refer_wav_path, prompt_text, prompt_language, text, text_language):
    # 创建或连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE gpt_sovits_params
        SET name=?, url = ?, refer_wav_path = ?, prompt_text = ?, prompt_language = ?, text = ?, text_language = ?
        WHERE name = ?
        ''', (name,url, refer_wav_path, prompt_text, prompt_language, text, text_language, name))
    except sqlite3.Error as e:
        print(f"Error updating record: {e}")
        return False
    else:
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
#从数据库获取参数
def get_gpt_sovits_params(name):
    # 创建或连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT * FROM gpt_sovits_params WHERE name = ?
        ''', (name,))
        row = cursor.fetchone()
        if row is None:
            return None
        else:
            return row
    except sqlite3.Error as e:
        print(f"Error retrieving record: {e}")
        return None
    finally:
        cursor.close()
        conn.close() 


# 删除
def delete_gpt_sovits_params(name):
    # 创建或连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除数据
    cursor.execute('''
    DELETE FROM gpt_sovits_params WHERE name = ?
    ''', (name,))

    # 提交事务
    conn.commit()

    # 关闭连接
    cursor.close()
    conn.close()



def add_port_settings(name,ollama_port, ollama_command, gpt_sovits_port, gpt_sovits_path, sovits_weights, gpt_weights, gpt_sovits_text, gpt_sovits_voice, gpt_sovits_language, gpt_sovits_command):
     # 创建或连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    #根据设置名称查询是否存在
    cursor.execute('SELECT * FROM port_settings WHERE name=?', (name,))
    result = cursor.fetchone()
    #如果存在，结束
    if result:
        return
    # 插入数据
    cursor.execute('''
    INSERT INTO port_settings (name,ollama_port, ollama_command, gpt_sovits_port, gpt_sovits_path, sovits_weights, gpt_weights, gpt_sovits_text, gpt_sovits_voice, gpt_sovits_language, gpt_sovits_command)
    VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name,ollama_port, ollama_command, gpt_sovits_port, gpt_sovits_path, sovits_weights, gpt_weights, gpt_sovits_text, gpt_sovits_voice, gpt_sovits_language, gpt_sovits_command))

    # 提交事务
    conn.commit()

    # 关闭连接
    cursor.close()
    conn.close()

#更新
def update_port_settings(name,ollama_port, ollama_command, gpt_sovits_port, gpt_sovits_path, sovits_weights, gpt_weights, gpt_sovits_text, gpt_sovits_voice, gpt_sovits_language, gpt_sovits_command):
    # 创建或连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE port_settings
        SET name=?, ollama_port = ?, ollama_command = ?, gpt_sovits_port = ?, gpt_sovits_path = ?, sovits_weights = ?, gpt_weights = ?, gpt_sovits_text = ?, gpt_sovits_voice = ?, gpt_sovits_language = ?, gpt_sovits_command = ?
                        WHERE name = ?
        ''', (name,ollama_port, ollama_command, gpt_sovits_port, gpt_sovits_path, sovits_weights, gpt_weights, gpt_sovits_text, gpt_sovits_voice, gpt_sovits_language, gpt_sovits_command, name))
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False
    # 提交事务
    conn.commit()
    # 关闭连接
    cursor.close()
    conn.close()
    return True

#获取参数


#快速添加
def fast_add_port_settings():
    #从 Port 类中获取端口号
    name=Port.name
    ollama_port = Port.ollama_port
    gpt_sovits_port = Port.gpt_sovits_port
    ollama_command = Port.ollama_command
    gpt_sovits_path = Port.gpt_sovits_path
    sovits_weights = Port.sovits_weights
    gpt_weights = Port.gpt_weights
    gpt_sovits_text = Port.gpt_sovits_text
    gpt_sovits_voice = Port.gpt_sovits_voice
    gpt_sovits_language = Port.gpt_sovits_language
    gpt_sovits_command = Port.gpt_sovits_command
    add_port_settings(name,ollama_port, ollama_command, gpt_sovits_port, gpt_sovits_path, sovits_weights, gpt_weights, gpt_sovits_text, gpt_sovits_voice, gpt_sovits_language, gpt_sovits_command)


def fast_add_gpt_sovits_params():
    #从 Prompt 类中获取文本和语言
    name=tts.name
    url=tts.url
    refer_wav_path=tts.refer_wav_path
    prompt_text=tts.prompt_text
    prompt_language=tts.prompt_language
    text=tts.text
    language=tts.text_language
    add_gpt_sovits_params(name,url, refer_wav_path, prompt_text, prompt_language, text, language)



#快速更新
def fast_update_port():
    try:
        #从 Port 类中获取端口号
        name=Port.name
        ollama_port = Port.ollama_port
        gpt_sovits_port = Port.gpt_sovits_port
        ollama_command = Port.ollama_command
        gpt_sovits_path = Port.gpt_sovits_path
        sovits_weights = Port.sovits_weights
        gpt_weights = Port.gpt_weights
        gpt_sovits_text = tts.gpt_sovits_text
        gpt_sovits_voice = tts.gpt_sovits_voice
        gpt_sovits_language = tts.gpt_sovits_language
        gpt_sovits_command = Port.gpt_sovits_command
        update_port_settings(name,ollama_port, ollama_command, gpt_sovits_port, gpt_sovits_path, sovits_weights, gpt_weights, gpt_sovits_text, gpt_sovits_voice, gpt_sovits_language, gpt_sovits_command)
    except Exception as e:
        print(f"An error occurred while fast updating port settings: {e}")

def fast_udpate_gpt_sovits_params():
    try:
        #从 Prompt 类中获取文本和语言
        name=tts.name
        url=tts.url
        refer_wav_path=tts.refer_wav_path
        prompt_text=tts.prompt_text
        prompt_language=tts.prompt_language
        text=tts.text
        text_language=tts.text_language
        update_gpt_sovits_params(name,url, refer_wav_path, prompt_text, prompt_language, text, text_language) 
    except Exception as e:
        print(f"An error occurred while fast updating gpt sovits params: {e}")


def load_port_settings():
    try:
        # 创建或连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 检查数据库中是否有之前的设置
        cursor.execute('SELECT * FROM port_settings ')
        settings = cursor.fetchall()

        # 如果数据库中有设置，则加载最后一行设置
        if settings:
            last_setting = settings[-1]
            id,name,ollama_port, ollama_command, gpt_sovits_port, gpt_sovits_path, sovits_weights, gpt_weights, gpt_sovits_text, gpt_sovits_voice, gpt_sovits_language, gpt_sovits_command = last_setting
            Port.name=name
            Port.ollama_port = ollama_port
            Port.ollama_command = ollama_command
            Port.gpt_sovits_port = gpt_sovits_port
            Port.gpt_sovits_path = gpt_sovits_path
            Port.sovits_weights = sovits_weights
            Port.gpt_weights = gpt_weights
            Port.gpt_sovits_text = gpt_sovits_text
            Port.gpt_sovits_voice = gpt_sovits_voice
            Port.gpt_sovits_language = gpt_sovits_language
            print("Loaded previous settings from database.")
        else:
            fast_add_port_settings()
            print("Saved current settings to database.")

        # 关闭连接
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred while loading port settings: {e}")

def load_gpt_sovits_params():
    try:
        # 创建或连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 检查数据库中是否有之前的设置
        cursor.execute('SELECT * FROM gpt_sovits_params ')
        settings = cursor.fetchall()
        # 如果数据库中有设置，则加载最后一行设置
        if settings:
            last_setting = settings[-1]
            id,name,url, refer_wav_path, prompt_text, prompt_language, text, text_language = last_setting
            tts.name = name
            tts.url = url
            tts.refer_wav_path = refer_wav_path
            tts.prompt_text = prompt_text
            tts.prompt_language = prompt_language
            tts.text = text
            tts.text_language = text_language
            print("Loaded previous settings from database.")
        else:
            fast_add_gpt_sovits_params()
            print("Saved current settings to database.")

        # 关闭连接
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred while loading gpt sovits params: {e}")