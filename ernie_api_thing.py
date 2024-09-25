import json

from flask import Flask, request, jsonify
import pandas as pd
import erniebot
from db import milvusClient
import time
import logging

app = Flask(__name__)

erniebot.api_type = "aistudio"

with open('config.json', 'r') as f:
    config = json.load(f)
    erniebot.access_token = config[0]['ACCESS_TOKEN']
    dbFile = config[0]['DB_FILE']

logging.basicConfig(level=logging.INFO)
mc = milvusClient()
mc.createCollection()
mc.load()


def embedding(text):
    response = erniebot.Embedding.create(
        model="ernie-text-embedding",
        input=[text])

    return response.get_result()


def split_text(text, chunk_size=100):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


# 自动加载知识库
def load_knowledge_base():
    if dbFile.endswith(".csv"):
        try:
            data_df = pd.read_csv(dbFile, encoding='gbk')
        except:
            data_df = pd.read_csv(dbFile, encoding="utf-8")
        reply = data_df.iloc[:, 0]
    elif dbFile.endswith(".xlsx") or dbFile.endswith(".xls"):
        data_df = pd.read_excel(dbFile)
        reply = data_df.iloc[:, 0]

    for rly in reply:
        try:
            rlyEmbedding = embedding(rly)
            mc.insert(rly, rlyEmbedding)
            time.sleep(0.1)
        except Exception as e:
            logging.info("【数据导入失败】{}".format(e))
    logging.info("【数据导入】成功导入文本向量")


load_knowledge_base()


def chat(model, text):
    response = erniebot.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": text}],
    )
    return response.get_result()


def bot(text, llm):
    logging.info("【用户输入】 {}".format(text))
    text_embedding = embedding(text)
    ragResult = mc.search(text_embedding)

    instruction = '''
你是一位智能编程助手，你会为用户回答关于编程、代码、计算机方面的任何问题，并提供 'Markdown格式的规范、可以执行、准确安全、换行标准的代码'
注意代码本身不能和markdown语法冲突，如果冲突请解决，而且markdown的文字颜色为'白色'或者其他不与黑色背景冲突的颜色,代码块的背景颜色设置成黑色,并在必要时提供详细的解释。
任务：请为代码纠正或者生成代码，记得每行代码都要附上注释，有必要时还需要写出具体的知识点，如果问的是数据中已经有的题目，记得把题目的内容也贴上去。
代码注意换行，代码默认使用C语言或者C++语言，记得给用户标注是用的什么语言。
'''
    erniebotInput = instruction + "用户的提问是：" + text + "\n\n[给定的文段]是：" + ragResult
    logging.info("【文心Prompt】 {}".format(erniebotInput))
    chatResult = chat(llm, erniebotInput)
    logging.info("【文心Answer】 {}".format(chatResult))
    return chatResult


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    text = data.get('text')
    model = data.get('model', 'ernie-4.0-turbo-8k')  # 默认模型名称
    if not text:
        return jsonify({"error": "No text provided"}), 400

    response = bot(text, model)
    return jsonify({"response": response})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
