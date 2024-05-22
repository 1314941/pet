import logging.config
from LmStudio import send_message_to_ollama,AIMessage,HumanMessage,Message,LmModel,action_Model,start_dialog_Model,style_Model,relation_Model,graph_Model
from KeyWord import extract_keywords
import Prompt
from Load_Memory import MemoryNode,clean_memory,rerank_id
from Memory import Memory
from Search import Search
import logging
import sys
from decorator import log_task
from datetime import datetime


current_time=datetime.now().strftime('%Y-%m-%d')
# 设置日志记录器
logging.basicConfig(filename=f'app_{current_time}.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')




#真就是靠着bug跑起来的代码
class chatModel():
    def __init__(self,character_name:str=Prompt.character_name,prompt_text=Prompt.prompt_text)->None:
        self.character_name=character_name
        self.search_obj=Search()
        self.memory_obj=Memory(self.search_obj)
        self.prompt_text=prompt_text


    def extract_key_words(self,inputs:str)->list[str]:
        """extract key words tool"""
        return extract_keywords(inputs)

    def search_memory(self,keywords:list[dict],in_message:Message)->list[Message]:  
        """search memory tool"""
        content=[]
        print("输入：",in_message.content)
        text=''
        for keyword in keywords:
            messages=self.memory_obj.retrieve_memory(keyword['keyword'],in_message.content)
            if messages:
                for message in messages:
                    text+=message.content+'\n'
                message=start_dialog_Model().chat_agent(text)  #提取主题
                message=HumanMessage(message)
                content.append(message)
                self.memory_obj.add_memory(message)
        content.append(in_message)
        return content

    # Define the function that calls the model
    def call_ollama(self,messages:list[Message])->Message:
        response = send_message_to_ollama(inputs=messages,prompt_text=self.prompt_text)   #这里真的搞死人啊！ 硬是没提示 
        # We return a list, because this will get added to the existing list
        return AIMessage(response)
    
       # Define the function that calls the model
    def call_LM(self,messages:list[Message])->Message:
        response = self.lm_model.send_message(messages)  
        # We return a list, because this will get added to the existing list
        return AIMessage(response)

    def chat(self,message="你好，我是小白，你叫什么名字？")->None:
        try:
            if message=='/clean':
                clean_memory()
                return
            elif message=='/rerank/id':
                rerank_id()
                return
            elif message=='/ai':
                self.Ai_to_Ai()
                return
            keywords=self.extract_key_words(message)

            message=HumanMessage(message)
            self.memory_obj.add_memory(message,keywords)

            messages=self.search_memory(keywords,message)

            message=self.call_ollama(messages)
            content=message.content
            keywords=self.extract_key_words(content)
            self.memory_obj.add_memory(message,keywords)
            return content
        except Exception as e:
            print("chat error:",e)
            logging.error(e)

    #ai座谈会模式
    def Ai_to_Ai(self)->None:
        self.lm_model=LmModel()
        content=input("开头语：")
        #对话轮数
        #max_talk_count=int(input("对话轮数："))
        max_talk_count=1
        talk_count=0
        while True:
            keywords=self.extract_key_words(content)

            message=HumanMessage(content)
            self.memory_obj.add_memory(message,keywords)

            messages=self.search_memory(keywords,message)

            message=self.call_LM(messages)
            content=message.content
            talk_count+=1
            if talk_count>=max_talk_count:
                self.lm_model=LmModel()  #新一轮对话
@log_task
def test():
    while True:
        test_text='派蒙，你又偷吃我鸡腿！'
        start_dialog_Model().chat_agent(test_text)
        style_Model().chat_agent(test_text)
        relation_Model().chat_agent(test_text)
        graph_Model().chat_agent(test_text)
        action_Model().chat_agent(test_text)



try:
    #test()
    #Prompt.character_name=input("请输入角色名称:")
    test_app=chatModel(Prompt.prompt_text)
    #test_app.chat()
    while True:
        print("-----\n")
        print("请输入(/clean 清理记忆库  /rerank/id   重新排序id):")
        content=input("请输入：")
        if content!="exit":
            test_app.chat(content)
        else:
            break
except Exception as e:
    print("test_app error:",e)