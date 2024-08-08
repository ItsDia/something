import logging
import random

from botpy.message import GroupMessage

import messageSend
from bot_qq.qqutils.ext import Command

_log = logging.getLogger(__name__)


@Command("去哪吃")
async def where_to_eat(message: GroupMessage, params):
    choices = [
        "🍽 三餐一楼",
        "🍽 三餐二楼",
        "🍽 三餐三楼",
        "🍴 服务楼二楼",
        "🍴 服务楼三楼",
        "🍴 服务楼四楼",
        "🍱 四餐一楼",
        "🍱 四餐二楼",
        "去外面吃",
        "点外卖吧，我知道你一开始就是这么想的",
        "不吃了，减肥",
        "厕所。"
    ]
    content = f"\n今天推荐: {random.choice(choices)}"
    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )
    return True
