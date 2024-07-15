import logging
import botpy
from botpy.message import GroupMessage
from bot_qq.qqutils.ext import Command

import sqlite3
import command

_log = logging.getLogger(__name__)
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
            luck TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

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
            content="Command not found.\nPlease try to use /help to get help.",
        )
        return

if __name__ == "__main__":
    intents = botpy.Intents.all()
    intents.public_messages = True

    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True)
    client = MyClient(intents=intents)
   
  
    client.run(appid=APPID, secret=SECRET)
