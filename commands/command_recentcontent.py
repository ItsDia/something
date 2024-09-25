import logging
from datetime import datetime

import aiohttp
from botpy.message import GroupMessage

from bot_qq.qqutils.ext import Command

@Command("查看近期cf比赛", "recentcf", "比赛")
async def recent_cf(message: GroupMessage, params):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://contests.sdutacm.cn/contests.json") as response:
                contests = await response.json()

            result_str = "\n数据来源: SDUTACM Contest API\n\n"
            if params:
                if params[0] == "cf":
                    source = "codeforce"
                elif params[0] == "luogu":
                    source = "洛谷"
                elif params[0] == "vjudge":
                    source = "Virtual Judge"
                else:
                    source = params[0].lower()
                contests = list(filter(lambda x: source in x['source'].lower(), contests))
            for contest in contests:
                start_time = datetime.fromisoformat(contest['start_time'])
                end_time = datetime.fromisoformat(contest['end_time'])
                duration = end_time - start_time
                start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S %Z')

                result_str += f"来源: {contest['source']}\n"
                result_str += f"比赛名称: {contest['name']}\n"
                result_str += f"开始时间: {start_time_str}\n"
                result_str += f"持续时间: {duration}\n"
                result_str += f"比赛ID: {contest['contest_id']}\n"
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
