import ollama
from datetime import datetime
import Prompt
from openai import OpenAI
import requests
import os
from Search import Search_history
import soundfile as sf
from decorator import log_task


'''
top_k=100,  #废话
repeat_penalty=1.6,
repeat_last_n=1,  # 防止重复
temperature=0.9,  # 控制随机性
mirosstat_tau=0.9,  # 输出连贯性
mirostat_eta=0.9,  # 学习率  算法对生成文本的反馈响应程度
top_p=0.9,  #废话
'''


class Message():
    def __init__(self,content:str="",role="system"):
        self.content=content
        self.role=role
        self.time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.json={
            "role":self.role,
            "content":self.content,
        }
        

class HumanMessage(Message):
    def __init__(self,content="",role="user"):
        super().__init__(content,role)

class AIMessage(Message):
    def __init__(self, content="", role="assistant"):
        super().__init__(content, role)


class FunctionMessage(Message):
    def __init__(self,content="",role="function"):
        super().__init__(content,role)


#ollama速度太慢啦
def send_message_to_ollama(model='llama2-chinese',inputs:list[Message]=[HumanMessage('在吗')],prompt_text=None):
    try:
        in_messages=[]
        for i,input in enumerate(inputs):
            in_messages.append(input.json)
        if prompt_text:
            in_messages.append(Message(prompt_text).json)
        stream = ollama.chat(   #引用的库与自己建的库不要重名
            model=model,
            messages=in_messages,
            stream=True,
            keep_alive=3
        )
        content=''
        for chunk in stream:
            print(chunk['message']['content'], end='', flush=True)
            content += chunk['message']['content']
        return content
    except Exception as e:
        print("send message error",e)



class BaseModel():
    def __init__(self,temperate=0.7,prompt_text=Prompt.default_prompt,stream=True):
        if Prompt.prompt_text!=None and prompt_text==Prompt.default_prompt:
            prompt_text=Prompt.prompt_text
        self.client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")  #创建模型
        self.temperate=temperate
        self.stream=stream
        self.system_message=Message(prompt_text)
        self.history=[]
        self.history.append(self.system_message.json)

    @log_task
    def chat_agent(self,message:str,chatbox=None):
            self.history.append(HumanMessage(message).json)
            completion = self.client.chat.completions.create(
                model="publisher/Repository",
                messages=self.history,
                temperature=0.7,
                stream=True,
                max_tokens=Prompt.max_help_tokens,
                stop=None
            )

            new_message = {"role": "assistant", "content": ""}
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
                    new_message["content"] += chunk.choices[0].delta.content
                    if chatbox:
                        chatbox.set_text(new_message["content"])
            return new_message["content"]
      
    



class LmModel(BaseModel):
    def __init__(self,temperate=0.7,prompt_text=Prompt.default_prompt,stream=True):
        super().__init__(temperate,prompt_text,stream)
        if Prompt.prompt_text!=None and prompt_text==Prompt.default_prompt:
            prompt_text=Prompt.prompt_text
        self.client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")  #创建模型
        self.temperate=temperate
        self.stream=stream
        self.system_message=Message(prompt_text)
        self.history=[]
    


    def send_message(self,message:list[Message],chatbox=None):
            if message!=None:
                try:
                    print("开始发送消息")
                    #获取最后一个消息
                    last_message=message[-1]
                    self.clean_history(last_message.content)
                    wav_files = []
                    for i in range(len(message)):
                        self.history.append(message[i].json)   #注意格式
                    while True:
                        completion = self.client.chat.completions.create(
                            model="publisher/Repository",
                            messages=self.history,
                            temperature=self.temperate,
                            stream=self.stream,
                            max_tokens=600,
                            stop=None
                        )
                        new_message = ""
                        for chunk in completion:
                            if chunk.choices[0].delta.content:
                                print(chunk.choices[0].delta.content, end="", flush=True)
                                new_message += chunk.choices[0].delta.content
                                if chatbox:
                                    chatbox.set_text(new_message)
                                #voice_path=self.generate_voice(chunk.choices[0].delta.content)
                                #wav_files.append(voice_path)
                        # 合并 WAV 文件
                        #timestamp=datetime.now().strftime("%H_%M_%S")
                        #output_wav_path=f'voice/{datetime.now().strftime("%Y-%m-%d")}/{timestamp}.wav'
                        #sf.write(output_wav_path, sf.read(wav_files[0]), sr=sf.read(wav_files[0])[1])
                        #for i in range(1, len(wav_files)):
                        #    sf.write(output_wav_path, sf.read(wav_files[i]), sr=sf.read(wav_files[i])[1])
                        # 输出合并后的 WAV 文件路径
                        #print(f'合并完成，输出文件路径为：{output_wav_path}')
                        self.generate_voice(new_message)
                        self.history.append(AIMessage(new_message).json)
                        return new_message
                except Exception as e:
                    print(f"Error: {e}  LM Studio  API 出错啦")
                    return None
                
        

    
    #生成语音   每次都开端口  有点麻烦  还需要整合包
    def generate_voice(self,text,timestamp=None):
        try:
            timestamp=datetime.now().strftime("%H_%M_%S")
            # GPT-SoVITS API的URL和端口
            url = 'http://127.0.0.1:9881'

            # 参考音频的路径（相对路径或绝对路径，取决于你的GPT-SoVITS服务配置）
            #refer_wav_path = 'C:\chat\gpt_sovits\GPT-SoVITS-beta0306fix2\GPT-SoVITS-beta0306fix2\DATA\audio\longzu\slicers\good.wav'

            # 提示文本
            prompt_text = '我生气啦！！！'

            # 提示文本的语言
            prompt_language = 'zh'

            # 要合成的文本
            text = text

            # 文本的语言
            text_language = 'zh'

            # 构建请求参数
            data = {
                #'refer_wav_path': refer_wav_path,
                'prompt_text': prompt_text,
                'prompt_language': prompt_language,
                'text': text,
                'text_language': text_language
            }

            # 发送POST请求
            response = requests.post(url, json=data)
            # 检查响应状态码
            if response.status_code == 200:
                #保留文本前五个子作为文件名
                file_text=text[:5]          #修改一下  提取内容 作为称呼  
                root_path='voice'
                if not os.path.exists(root_path):
                    os.mkdir(root_path)
                datetime_str=datetime.now().strftime("%Y-%m-%d")
                voice_dir=f'{root_path}/{datetime_str}'
                if not os.path.exists(voice_dir):
                    os.mkdir(voice_dir)
                voice_dir=f'{voice_dir}/temp'
                if not os.path.exists(voice_dir):
                    os.mkdir(voice_dir)
                voice_path=f'{root_path}/{datetime_str}/temp/{timestamp}.wav'
                voice_path=os.path.normpath(voice_path)
                # 如果响应状态码为200，表示成功，将音频流保存到文件
                with open(voice_path, 'wb') as f:
                    f.write(response.content)
                print(f'音频已保存为{voice_path}.wav')
                return voice_path
            else:
                # 如果响应状态码不是200，表示失败，输出错误信息
                print('请求失败:', response.status_code)
                print('错误信息:', response.text)
                #返回音频地址 
                return None
        except Exception as e:
            print(f'生成语音失败: {e}')
            return None
        
    def clean_history(self,inputs:str):
        if self.history==[]:
            self.history.append(self.system_message.json)
            return
        self.new_history=[]
        self.new_history.append(self.system_message.json)
        message_list=[memory['content'] for memory in self.history]
        search=Search_history(message_list)
        ids=search.retrieve_and_rank(inputs)
        for id in ids:
            if self.history[id]['role']!='user':
                self.new_history.append(self.history[id])
                #self.new_history.append(self.history[id+1])  不好把握啊
            elif self.history[id]['role']=='assistant':
                self.new_history.append(self.history[id-1])
                #self.new_history.append(self.history[id])
        text=''
        for memory in self.new_history:
            text+=memory['content']
        message=start_dialog_Model().chat_agent(text)   #大模型提出话题
        self.history=message
            

class action_Model(BaseModel):
    def __init__(self,temperate=0.7,prompt_text=Prompt.action_prompt,stream=True):
        super().__init__(temperate,prompt_text,stream)

    def chat_agent(self, message: str, chatbox=None):
           pass



##对话  关系提取  图数据库   风格检测  发起对话
class relation_Model(BaseModel):
    def __init__(self,temperate=0.7,prompt_text=Prompt.system_prompt,stream=True):
        super().__init__(temperate,prompt_text,stream)

    def chat_agent(self,message:str,chatbox=None):
        relation_prompt = f"""请从{message}中抽取SPO三元组,并以json文件格式返回"""
        result=super().chat_agent(relation_prompt)
        return graph_Model().chat_agent(result)

class graph_Model(BaseModel):
    def __init__(self,temperate=0.7,prompt_text=Prompt.system_prompt,stream=True):
        super().__init__(temperate,prompt_text,stream)

    def chat_agent(self,message:str,chatbox=None):
        graph_prompt = f"""根据
        {message}
        这些三元组,生成sql语句，将关系存入neo4j中"""
        return super().chat_agent(graph_prompt)



class style_Model(BaseModel):
    def __init__(self,temperate=0.7,prompt_text=Prompt.system_prompt,stream=True):
        super().__init__(temperate,prompt_text,stream)

    def chat_agent(self,message:str,chatbox=None):           
      style_prompt = f"""判断给定的句子是否符合
      {Prompt.prompt_text}  
      中主角的风格，你只能回答‘是’或‘不是’"""
      return super().chat_agent(style_prompt)



class start_dialog_Model(BaseModel):
    def __init__(self,temperate=0.7,prompt_text=Prompt.system_prompt,stream=True):
        super().__init__(temperate,prompt_text,stream)

    def chat_agent(self,message:str,chatbox=None):
        start_dialog_prompt = f"""请分析对话
        /n/n{message}/n
        提取出其中的对话主题，并根据/n{Prompt.prompt_text}/n的人物性格、情绪、态度、喜好、习惯等特征，生成符合对话中语境的句子，发起新的话题"""
        if chatbox:
            result=super().chat_agent(start_dialog_prompt,chatbox)
        else:
            result=super().chat_agent(start_dialog_prompt)
        return result



#提取三段式
#Please extract all triples from the provided text and return them in JSON format. Each triple should consist of three components: the subject, the predicate, and the object.
