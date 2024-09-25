import logging
from botpy.message import GroupMessage
from bot_qq.qqutils.ext import Command

_log = logging.getLogger(__name__)

@Command("help")
async def help_command(message: GroupMessage, params):
    _log.info("Help command triggered")
    content = """
📚 可用命令列表 📚
====================
🔮 /今日运势 - 查看今天的运势
🔗 /查看近期cf比赛
(/recentcf 也可以)
🏆 /查看cf用户 <cfid> - 不带参数则查询自己的，带参数则查询别人的
(/cf <cfid> 也可以)
🎮 /绑定cf <cfid> - 绑定cf账号
(/bindcf <cfid> 也可以)
ℹ️ /去哪吃
/ai <text> 询问AI
/t2i <text> 生成思维导图
====================
"""
    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )
    return True
