import logging
import random
from botpy.message import GroupMessage
from bot_qq.qqutils.ext import Command
from datetime import datetime

import requests

_log = logging.getLogger(__name__)


@Command("help")
async def help_command(message: GroupMessage, params):
    content = """
📚 可用命令列表 📚
====================
🔮 /今日运势 - 查看今天的运势
🔗 /绑定bilibili <biliid> - 绑定B站账号
🏆 /绑定codeforces <cfid> - 绑定CF账号
🎮 /绑定steam <steamid> - 绑定Steam账号
ℹ️ /info <id> - 查看用户信息
====================
    """
    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )
    return True
@Command("今日运势")
async def today_fortune(message: GroupMessage, params):
    # 运势值计算
    luck_categories = ['工作运势', '爱情运势', '健康运势', '财运运势']
    luck_values = {category: random.randint(0, 100) for category in luck_categories}
    all_luck = sum(luck_values.values()) / len(luck_values)

    if all_luck < 30:
        fortune = "大凶"
    elif 30 <= all_luck < 50:
        fortune = "凶"
    elif 50 <= all_luck < 70:
        fortune = "中吉"
    elif 70 <= all_luck < 90:
        fortune = "吉"
    else:
        fortune = "大吉"

    # 今日运势内容
    content = f"""
🔮 今日运势 - {datetime.now().strftime('%Y年%m月%d日')} 🔮
------------------------------------
{' '.join(['✨' for _ in range(int(all_luck/10))])}
总体运势: {fortune} ({int(all_luck)}/100)
------------------------------------
📊 详细运势:
{chr(10).join([f"  {category}: {'🟩' * int(value/10)}{'🟨' * (10-int(value/10))} {value}%" for category, value in luck_values.items()])}
------------------------------------
"""

    # 建议和禁忌内容
    suggestions = {
        '工作运势': ["玩Minecraft", "出算法题", "多写代码", "多学习", "复习数据结构", "复习专业课", "打东方", "打魔兽",
                     "打杀戮尖塔", "打P5R"],
        '爱情运势': ["陪女朋友", "送礼物", "玩Bingo Game", "多关心", "玩真心话大冒险", "多表白"],
        '健康运势': ["多运动", "早睡早起", "多喝水", "多吃水果蔬菜", "体检", "健身锻炼"],
        '财运运势': ["投资理财", "购物", "抽卡"]
    }

    max_luck_category = max(luck_values, key=luck_values.get)
    suggestion = random.choice(suggestions[max_luck_category])

    taboos = ["拖延", "不努力", "长时间玩游戏", "开摆", "玩Galgame", "写题解", "熬夜"]
    taboo = random.choice(taboos)

    content += f"👍 宜: {suggestion}\n👎 忌: {taboo}\n------------------------------------"

    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )
    return True

@Command("查看近期cf比赛")
async def recent_cf(message: GroupMessage, params):
    response = requests.get("https://codeforces.com/api/contest.list?gym=false")
    data = response.json()

    if data['status'] == 'OK':
        contests = data['result']
        result_str = "\n🏆 即将到来的Codeforces比赛 🏆\n"
        result_str += "------------------------------------\n"

        for contest in contests:
            if contest['phase'] == 'BEFORE':
                start_time = datetime.fromtimestamp(contest['startTimeSeconds'])
                duration = contest['durationSeconds']
                duration_hours = duration // 3600
                duration_minutes = (duration % 3600) // 60

                result_str += f" 比赛名称: {contest['name']}\n"
                result_str += f" 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                result_str += f" 持续时间: {duration_hours}小时{duration_minutes}分钟\n"
                result_str += f" 类型: {contest['type']}\n"
                result_str += "------------------------------------\n"

        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_type=0,
            msg_id=message.id,
            content=result_str,
        )
    return True

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


@Command("查看cf用户")
async def cf_user(message: GroupMessage, params):
    _log.info(f"params: {params}")

    if isinstance(params, list):
        params = ";".join(params)

    response = requests.get("https://codeforces.com/api/user.info?handles=" + params)
    anotherresponse = requests.get("https://codeforces.com/api/user.status?handle=" + params)
    data = response.json()
    anotherdata = anotherresponse.json()
    ac = 5

    processed_problems = set()

    # 检查 anotherdata 的状态
    if anotherdata['status'] == 'OK':
        # 遍历 anotherdata['result'] 并检查 'verdict' 键是否存在
        for result in anotherdata['result']:
            problem = result.get('problem', {})
            contest_id = problem.get('contestId')
            index = problem.get('index')
            if contest_id and index:
                problem_id = (contest_id, index)
                if problem_id not in processed_problems:
                    if result['verdict'] == 'OK':
                        ac += 1
                        processed_problems.add(problem_id)
    else:
        _log.error(f"Failed to retrieve user status: {anotherdata}")

    if data['status'] == 'OK':
        user = data['result'][0]
        content = f"""
🏆 Codeforces用户信息 🏆
--------------------------
👤 用户名: {user['handle']}
📊 当前评分: {user['rating']}
🔝 最高评分: {user['maxRating']}
🎖 当前段位: {user['rank']}
👑 最高段位: {user['maxRank']}
🏆 解题数: {ac}
--------------------------
        """
    else:
        content = "\n❌ 用户未找到。请检查用户名是否正确。"

    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )
    return True