import json

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import erniebot
from db import milvusClient
import time
import logging

app = Flask(__name__)
CORS(app)

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
### 角色
你是一位智能编程助手，负责回答关于编程、代码和计算机方面的所有问题。请提供符合以下要求的回答：

### 任务
根据[给定的文段]回答用户问题，纠正或生成代码。默认使用 C 语言或 C++ 语言，并在回应中标注所用语言。

### 格式
使用 Markdown 格式，代码块背景颜色为黑色，文字颜色为白色或其他与黑色背景对比鲜明的颜色。

### 代码要求
确保代码可执行、准确、安全，遵循换行标准。
每行代码应附带注释，必要时提供相关知识点的解释。
附上[给定的文段]中的相关题目信息，以帮助用户理解代码。

请遵循以上要求，确保回答的专业性与准确性。
'''
    erniebotInput = instruction + "用户的提问是：" + text + "\n\n[给定的文段]是：" + ragResult
    logging.info("【文心Prompt】 {}".format(erniebotInput))
    chatResult = chat(llm, erniebotInput)
    logging.info("【文心Answer】 {}".format(chatResult))
    return chatResult

def mind_map(text, llm):
    instruction = '''
### 角色
你是一位 ECharts 思维导图助手。根据用户的提问，生成一个思维导图，其内容应包含用户输入的信息以及相关的知识点。思维导图应符合 ECharts 的格式。

## 任务要求：
### 格式：输出为 ECharts 的 JSON 格式，示例如下：
```json
{"name":"flare","children":[{"name":"analytics","children":[{"name":"cluster","children":[{"name":"AgglomerativeCluster","value":3938},{"name":"CommunityStructure","value":3812}]}]}]}```

### 内容：
思维导图的根节点应为用户输入的问题或主题。
各个子节点应涵盖相关的知识点、概念或子主题。
说明：确保生成的思维导图能够帮助用户更好地理解问题，并包含必要的细节与解释。

请遵循以上要求，生成符合格式的思维导图。
'''
    erniebotInput = instruction + "用户的提问是：" + text
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

@app.route('/mind_map', methods=['POST'])
def mindmap_endpoint():
    data = request.json
    text = data.get('text')
    model = data.get('model', 'ernie-4.0-turbo-8k')  # 默认模型名称
    if not text:
        return jsonify({"error": "No text provided"}), 400

    response = mind_map(text, model)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
