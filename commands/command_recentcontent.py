import logging
from datetime import datetime

import aiohttp
from botpy.message import GroupMessage

from bot_qq.qqutils.ext import Command

_log = logging.getLogger(__name__)


@Command("查看近期cf比赛", "recentcf")
async def recent_cf(message: GroupMessage, params):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://codeforces.com/api/contest.list?gym=false") as response:
                data = await response.json()

        if data['status'] == 'OK':
            contests = data['result']
            upcoming_contests = [
                contest for contest in contests if contest['phase'] == 'BEFORE'
            ]

            result_str = "\n🏆 即将到来的Codeforces比赛 🏆\n"
            for contest in reversed(upcoming_contests):
                start_time = datetime.fromtimestamp(contest['startTimeSeconds'])
                duration = contest['durationSeconds']
                duration_hours = duration // 3600
                duration_minutes = (duration % 3600) // 60

                result_str += f" 比赛名称: {contest['name']}\n"
                result_str += f" 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                result_str += f" 持续时间: {duration_hours}小时{duration_minutes}分钟\n"
                result_str += f" 类型: {contest['type']}\n"
                result_str += "\n"

            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0,
                msg_id=message.id,
                content=result_str,
            )
        return True
    except Exception as e:
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_type=0,
            msg_id=message.id,
            content=f"\n❌ 查询失败: {str(e)}",
        )
        return True
