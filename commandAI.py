import logging
import random

import zhipuai
from botpy.message import GroupMessage
from bot_qq.qqutils.ext import Command
from datetime import datetime
import messageSend
import requests
import sqlite3
from zhipuai import ZhipuAI

client = ZhipuAI(api_key="")

@Command("ai")
async def ai_command(message: GroupMessage, params):
    content = ' '.join(params)
    response = client.chat.completions.create(
        model = "codegeex-4",
        messages=[
            {
                "role": "system",
                "content": "你是一位智能编程助手，你叫CodeGeeX。你会为用户回答关于编程、代码、计算机方面的任何问题，并提供格式规范、可以执行、准确安全的代码，并在必要时提供详细的解释。任务：请为输入代码提供格式规范的注释，包含多行注释和单行注释，请注意不要改动原始代码，只需要添加注释。 请用中文回答。"
            },
            {
                "role": "user",
                "content": content
            }
        ],
        top_p=0.7,
        temperature=0.9,
        max_tokens=1024,
        stop=["<|endoftext|>", "<|user|>", "<|assistant|>", "<|observation|>"]
    )
    result = response.choices[0].message.content
    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content="\n" + result,
    )
    return True
