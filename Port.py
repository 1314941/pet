import socket
import subprocess
import time
#这种方法启动的服务可能会在命令行窗口关闭后停止运行。如果您希望服务在后台持续运行，您可能需要将它们作为服务安装到操作系统中，
#或者使用其他方法来确保它们在后台稳定运行。


#设置名
name = "ollama"
#接口设置
ollama_port = 11434
ollama_command = "ollama serve"
gpt_sovits_port = 9881
#gpt_sovits 项目文件夹
gpt_sovits_path = "C:\\chat\\gpt_sovits\\GPT-SoVITS-beta0306fix2\\GPT-SoVITS-beta0306fix2"
sovits_weights = "SoVITS_weights/longzu_e8_s224.pth"
gpt_weights = "GPT_weights/longzu-e15.ckpt"
#参考文本
gpt_sovits_text = "世界上最暖和的地方，在天空树的顶上"
gpt_sovits_voice = "DATA/audio/longzu/slicers/good.wav"
#语言
gpt_sovits_language = "zh"
#双引号（"）将整个命令包围起来，或者使用转义字符（反斜杠\）来确保特殊字符被正确处理。
gpt_sovits_command = 'cd {} && .\\runtime\\python api2.py -p {} -s {} -g {} -dr {}  -dt {} -dl {}'.format(gpt_sovits_path,gpt_sovits_port,sovits_weights,gpt_weights,gpt_sovits_voice,gpt_sovits_text,gpt_sovits_language)



gpt_port_signal=False
voice_port_signal=False



# 检查端口是否开放
def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# 启动服务的函数
def start_service(command):
    print(f"Starting service with command: {command}")
    # 使用Popen在后台启动服务,不会阻塞脚本的执行。脚本会继续检查并启动第二个服务，而不会因为第一个服务占据命令行界面而卡住。
    subprocess.Popen(command, shell=True)
# 等待端口开启  轮询直到端口开启
def wait_for_port(port, timeout=60):
    start_time = time.time()
    while True:
        if is_port_open(port):
            print(f"Port {port} is now open.")
            return True
        elif time.time() - start_time > timeout:
            print(f"Timeout waiting for port {port} to open.")
            return False
        else:
            print(f"Port {port} is not open yet. Waiting...")
            time.sleep(5)  # 每隔5秒检查一次

# 启动服务并等待端口开启
def start_and_wait_for_port(port, command, timeout=120):
    #检测接口是否开启
    if is_port_open(port):
        print(f"Port {port} is already open.")
        return True
    start_service(command)
    if wait_for_port(port, timeout):
        print("Service started successfully.")
    else:
        print("Service failed to start.")



def start():
    pass
    #gpt_port_signal=start_and_wait_for_port(ollama_port, ollama_command)
    #voice_port_signal=start_and_wait_for_port(gpt_sovits_port, gpt_sovits_command)
    