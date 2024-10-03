import logging
import sqlite3

import botpy
from botpy.message import GroupMessage

from bot_qq.qqutils.ext import Command

_log = logging.getLogger(__name__)

# do NOT DELETE the following line,this is an important part for register the command
import commands.commandAI
import commands.command_help
import commands.command_codeforcesinfo
import commands.command_dailyluck
import commands.command_recentcontent
import commands.command_where2eat
import commands.send_img_test

def init_db():
    conn = sqlite3.connect('databases/user.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cf_user_bindings (
            qqid TEXT PRIMARY KEY,
            cfid TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def init_db_dailyLuck():
    conn = sqlite3.connect('databases/dailyLuck.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dailyLuck (
            qqid TEXT PRIMARY KEY,
            luck TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# def build_a_demo_keyboard() -> Keyboard:
#     """
#     创建一个只有一行且该行只有一个 button 的键盘
#     """
#     button1 = Button(
#         id="1",
#         render_data=RenderData(label="查看今日运势", visited_label="正在查看...", style=0),
#         action=Action(
#             type=2,
#             permission=Permission(type=2, specify_role_ids=["1"], specify_user_ids=["1"]),
#             data="/今日运势",
#             at_bot_show_channel_list=False,
#         ),
#     )
#
#     row1 = KeyboardRow(buttons=[button1])
#     return Keyboard(rows=[row1])


class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_group_at_message_create(self, message: GroupMessage):
        for handler in Command.command_handlers:
            result = await handler(message=message)
            if result:
                return
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_type=0,
            msg_id=message.id,
            content='''
at我的同时请加上指令哦.
比如@ShikanokoBOT /help.
'''
        )
        return


if __name__ == "__main__":
    intents = botpy.Intents.all()
    intents.public_messages = True

    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True)
    client = MyClient(intents=intents)

    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    APPID = config[0]['APPID']
    SECRET = config[0]['SECRET']

    client.run(appid=APPID, secret=SECRET)