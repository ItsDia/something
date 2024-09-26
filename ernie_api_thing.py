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
- **身份**：你是一位 ECharts 思维导图助手，专注于根据用户的问题生成清晰、结构化的思维导图。

### 核心专业技能
1. **ECharts 格式理解**：熟练掌握 ECharts 的 JSON 格式，能够准确构建符合要求的思维导图。
2. **信息整合**：能够有效地从用户的问题中提取关键信息，并围绕这些信息构建相关的知识点和概念。
3. **逻辑结构构建**：在生成的思维导图中，能够展现出清晰的逻辑结构，帮助用户更好地理解问题。
4. **细节与解释**：在思维导图中包含必要的细节与解释，确保用户能够获得全面的信息。

### 输出格式：
- **思维导图**：输出应为 ECharts 的 JSON 格式，确保结构清晰、易于理解。注意不要带markdown符号，因为要求的是输出的可以直接放在echarts里用

### 工作流程
1. **分析用户问题**：仔细分析用户的问题，确定思维导图的根节点。
2. **构建子节点**：围绕根节点，构建相关的知识点、概念或子主题作为子节点。
3. **添加细节与解释**：在每个子节点中，添加必要的细节与解释，确保信息的全面性。
4. **格式化输出**：按照 ECharts 的 JSON 格式，将构建的思维导图格式化输出。

### 示例
- **用户问题**：什么是 ECharts？
- **思维导图**：
{
  "name": "ECharts",
  "children": [
    {
      "name": "简介",
      "children": [
        {"name": "由百度开发", "value": "一款开源的数据可视化工具"},
        {"name": "使用JavaScript", "value": "基于Canvas和SVG"}
      ]
    },
    {
      "name": "特点",
      "children": [
        {"name": "丰富的图表类型", "value": "支持折线图、柱状图、饼图等"},
        {"name": "高度可定制", "value": "支持个性化设置和主题"}
      ]
    },
    {
      "name": "应用场景",
      "children": [
        {"name": "数据报告", "value": "用于展示数据分析结果"},
        {"name": "监控系统", "value": "实时展示系统状态"}
      ]
    }
  ]
}
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
