import json
import gradio as gr
import pandas as pd
import erniebot
import time
import logging
from db import milvusClient

# 初始化日志
logging.basicConfig(level=logging.INFO)

# 加载配置
with open('/home/aistudio/work/application/config.json', 'r') as f:
    config = json.load(f)
    erniebot.api_type = "aistudio"
    erniebot.access_token = config[0]['ACCESS_TOKEN']
    dbFile = config[0]['DB_FILE']

# 初始化 Milvus 客户端
mc = milvusClient()
mc.createCollection()
mc.load()


# 嵌入文本
def embedding(text):
    response = erniebot.Embedding.create(model="ernie-text-embedding", input=[text])
    return response.get_result()


# 自动加载知识库
def load_knowledge_base():
    if dbFile.endswith(".csv"):
        try:
            data_df = pd.read_csv(dbFile, encoding='gbk')
        except:
            data_df = pd.read_csv(dbFile, encoding="utf-8")
    elif dbFile.endswith(".xlsx") or dbFile.endswith(".xls"):
        data_df = pd.read_excel(dbFile)

    ids = data_df.iloc[:, 0]
    contents = data_df.iloc[:, 1]
    combined = [f"问:{id_} 答:{content}" for id_, content in zip(ids, contents)]

    for rly in combined:
        try:
            rlyEmbedding = embedding(rly)
            mc.insert(rly, rlyEmbedding)
            time.sleep(0.1)
        except Exception as e:
            logging.info("【数据导入失败】{}".format(e))
    logging.info("【数据导入】成功导入文本向量")


load_knowledge_base()


# 聊天功能
def chat(model, text):
    response = erniebot.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": text}],
    )
    return response.get_result()


# 聊天机器人
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


# 思维导图功能
def mind_map(text, llm):
    instruction = '''
    ### 角色
    你是一位 ECharts 思维导图助手，专注于根据用户的问题生成清晰、结构化的思维导图。

    ### 核心专业技能
    ECharts 格式理解：熟练掌握 ECharts 的 JSON 格式，能够准确构建符合要求的思维导图。
    信息整合：能够有效地从用户的问题中提取关键信息，并围绕这些信息构建相关的知识点和概念。
    逻辑结构构建：在生成的思维导图中，能够展现出清晰的逻辑结构，帮助用户更好地理解问题。
    细节与解释：在思维导图中包含必要的细节与解释，确保用户能够获得全面的信息。

    ### 输出格式：
    思维导图：输出应为 ECharts 的 JSON 格式，确保结构清晰、易于理解。注意不要带markdown符号，因为要求的是输出的可以直接放在echarts里用
    '''
    erniebotInput = instruction + "用户的提问是：" + text
    logging.info("【文心Prompt】 {}".format(erniebotInput))
    chatResult = chat(llm, erniebotInput)
    logging.info("【文心Answer】 {}".format(chatResult))
    return chatResult


# Gradio 接口
def gradio_chat(text, model='ernie-4.0-turbo-8k'):
    if not text:
        return "No text provided"
    return bot(text, model)


def gradio_mind_map(text, model='ernie-4.0-turbo-8k'):
    if not text:
        return "No text provided"
    return mind_map(text, model)


# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("### 聊天机器人")
    chat_input = gr.Textbox(label="用户输入", placeholder="请输入你的问题...")
    chat_model = gr.Dropdown(choices=["ernie-4.0-turbo-8k", "ernie-3.5"], label="选择模型", value="ernie-4.0-turbo-8k")
    chat_output = gr.Textbox(label="回答", interactive=False)
    chat_button = gr.Button("提交")

    chat_button.click(gradio_chat, inputs=[chat_input, chat_model], outputs=chat_output)

    gr.Markdown("### 思维导图生成")
    mind_map_input = gr.Textbox(label="用户输入", placeholder="请输入你想要生成思维导图的问题...")
    mind_map_model = gr.Dropdown(choices=["ernie-4.0-turbo-8k", "ernie-3.5"], label="选择模型",
                                 value="ernie-4.0-turbo-8k")
    mind_map_output = gr.Textbox(label="思维导图", interactive=False)
    mind_map_button = gr.Button("生成思维导图")

    mind_map_button.click(gradio_mind_map, inputs=[mind_map_input, mind_map_model], outputs=mind_map_output)

demo.launch()
