from sentence_transformers import SentenceTransformer, util


#情感分析助手类
class EmotionAssistant:
    def __init__(self):
        # 模型路径，需要替换为你的模型路径
        model_path='model\\multi-qa-mpnet-base-dot-v1'

        # 初始化模型
        self.model = SentenceTransformer(model_path)

        # 定义心情句子列表
        sentences = [
            "今天心情很好",       #Normal
            "想吃饭",
            "好渴啊",
            "想跟你说话",
            "感觉没力气",
            "今天心情一般",
            "今天心情有点差"
        ]
        # 计算所有句子的嵌入表示
        sentence_embeddings = self.model.encode(sentences)

    def get_most_similar_sentence(self,user_sentence):
        # 用户输入的句子
        query = user_sentence
        
        # 计算用户句子的嵌入表示
        query_embedding = self.model.encode(query)

        scores=util.dot_score(query_embedding, self.sentence_embeddings)[0].cpu().tolist()
        sentence_score_pairs=list(zip(self.sentences, scores))

        sentence_score_pairs.sort(key=lambda x: x[1], reverse=True)
        max_score=sentence_score_pairs[0][1]
        message=sentence_score_pairs[0][0]

        for sentence, score in sentence_score_pairs:
            print(f"句子: {sentence}, 评分: {score}")
            if float(score)>float(max_score):
                max_score=score
                message=sentence
        return {'corpus_id':sentence_score_pairs[0][1],'message':message}

    #情感分析接口
    def emotion_analysis(self,user_sentence):
        # 模拟用户输入
        user_sentence = "我的心情有点像是下雨天时的燕子"

        # 调用函数获取最相似的句子
        most_similar_sentence = self.get_most_similar_sentence(user_sentence) 
        message=most_similar_sentence['message']        #序号 corpus

        print("用户输入句子:", user_sentence)
        print("最相似句子:", most_similar_sentence)
        print("推荐的心情句子:", message)

        return message