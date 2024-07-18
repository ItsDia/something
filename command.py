import logging
import random
import sqlite3
from datetime import datetime

import aiohttp
import requests
from botpy.message import GroupMessage
from lxml import etree

import messageSend
from bot_qq.qqutils.ext import Command

_log = logging.getLogger(__name__)

@Command("help")
async def help_command(message: GroupMessage, params):
    content = """
📚 可用命令列表 📚
====================
🔮 /今日运势 - 查看今天的运势
🔗 /查看近期cf比赛
🏆 /查看cf用户 <cfid> - 不带参数则查询自己的，带参数则查询别人的
👤 /mycf - 查询自己的cf账号
🎮 /绑定cf <cfid> - 绑定cf账号
ℹ️ /去哪吃
🤖 /ai <content> - 调用AI
====================
"""
    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )
    return True


LUCK_CATEGORIES = ['工作运势', '爱情运势', '健康运势', '财运运势']
SUGGESTIONS = {
    '工作运势': ["玩Minecraft", "出算法题", "多写代码", "多学习", "复习数据结构", "复习专业课", "打东方", "打魔兽", "打杀戮尖塔", "打P5R"],
    '爱情运势': ["陪女朋友", "送礼物", "玩Bingo Game", "多关心", "玩真心话大冒险", "多表白"],
    '健康运势': ["多运动", "早睡早起", "多喝水", "多吃水果蔬菜", "体检", "健身锻炼"],
    '财运运势': ["投资理财", "购物", "抽卡"]
}
TABOOS = ["拖延", "不努力", "长时间玩游戏", "开摆", "玩Galgame", "写题解", "熬夜"]

@Command("今日运势")
async def today_fortune(message: GroupMessage, params):
    messageSend.init_db_dailyLuck()
    me_info = message.author.member_openid
    qqid = me_info
    current_date = datetime.now()
    date = current_date.strftime('%Y-%m-%d')

    with sqlite3.connect('databases/dailyLuck.db') as conn:
        c = conn.cursor()
        c.execute('''SELECT luck, date FROM dailyLuck WHERE qqid = ?''', (qqid,))
        result = c.fetchone()

        if result:
            stored_luck, stored_date = result
            stored_date = datetime.strptime(stored_date, '%Y-%m-%d')

            if stored_date.month == current_date.month and stored_date.day == current_date.day:
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0,
                    msg_id=message.id,
                    content="\n🔮 今日运势已查询过，请勿重复查询。\n" + stored_luck,
                )
                return True

    # 运势值计算
    luck_values = dict(zip(LUCK_CATEGORIES, random.choices(range(101), k=len(LUCK_CATEGORIES))))
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
🔮 今日运势 - {current_date.strftime('%Y年%m月%d日')} 🔮

{' '.join(['✨' for _ in range(int(all_luck / 10))])}
总体运势: {fortune} ({int(all_luck)}/100)

📊 详细运势:
{chr(10).join([f"  {category}: {'🟩' * int(value / 10)}{'🟨' * (10 - int(value / 10))} {value}%" for category, value in luck_values.items()])}

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

    content += f"👍 宜: {suggestion}\n👎 忌: {taboo}\n"

    with sqlite3.connect('databases/dailyLuck.db') as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO dailyLuck (qqid, luck, date)
            VALUES (?, ?, ?)
            ON CONFLICT(qqid) DO UPDATE SET
            luck=excluded.luck, date=excluded.date
        ''', (qqid, content, date))
        conn.commit()

    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )
    return True


@Command("查看近期cf比赛", "cf比赛")
async def recent_cf(message: GroupMessage, params):
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
    keyboard = messageSend.build_a_demo_keyboard()
    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
        keyboard=keyboard,
    )
    return True


async def get_cf_user_info(handle):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://codeforces.com/api/user.info?handles={handle}") as response:
            user_data = await response.json()

        async with session.get(f"https://codeforces.com/profile/{handle}") as response:
            html = await response.text()

    tree = etree.HTML(html)
    result = tree.xpath("//div[@class='_UserActivityFrame_footer']/div/div/div/text()")
    ac = str(result[0]).split(" ")[0]

    return user_data, ac


@Command("查看cf用户", "mycf", "查cf")
async def cf_user(message: GroupMessage, params):
    # 如果没有提供参数，尝试从数据库获取绑定的Codeforces账号
    if not params:
        # 初始化数据库连接
        messageSend.init_db()

        # 获取稳定的用户ID
        me_info =message.author.member_openid
        qqid = me_info
        with sqlite3.connect('databases/user.db') as conn:
            c = conn.cursor()
            c.execute('SELECT cfid FROM cf_user_bindings WHERE qqid=?', (qqid,))
            result = c.fetchone()
            if result:
                params = result[0]
            else:
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0,
                    msg_id=message.id,
                    content="\n❌ 您尚未绑定Codeforces账号，请先绑定或提供用户名。"
                )
                return True

    if isinstance(params, list):
        params = ";".join(params)

    user_data, ac = await get_cf_user_info(params)

    if user_data['status'] != 'OK':
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_type=0,
            msg_id=message.id,
            content="\n❌ 用户未找到。请检查用户名是否正确。"
        )
        return True

    user = user_data['result'][0]
    content = f"""
🏆 Codeforces用户信息 🏆
👤 用户名: {user['handle']}
📊 当前评分: {user['rating']} 
🔝 最高评分: {user['maxRating']}
🎖 当前段位: {user['rank']}
👑 最高段位: {user['maxRank']}
🏆 解题数: {ac}
        """

    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )
    return True

@Command("绑定cf")
async def bind_cf(message: GroupMessage, params):
    # 获取稳定的用户ID
    me_info = message.author.member_openid
    qqid = me_info

    if isinstance(params, list):
        params = ";".join(params)

    isExist = requests.get("https://codeforces.com/api/user.info?handles=" + params)
    if isExist.json()['status'] == 'FAILED':
        content = "\n❌ 请提供正确的Codeforces用户名。"
    else:
        messageSend.init_db()

        cfid = str(params)
        try:
            with sqlite3.connect('databases/user.db') as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO cf_user_bindings (qqid, cfid)
                    VALUES (?, ?)
                    ON CONFLICT(qqid) DO UPDATE SET
                    cfid=excluded.cfid
                ''', (qqid, cfid))
                conn.commit()

                # 立即查询并打印结果
                c.execute('SELECT * FROM cf_user_bindings WHERE qqid=?', (qqid,))
                result = c.fetchone()

            content = f"\n✅ 成功绑定Codeforces账号: {params}"
        except sqlite3.Error as e:
            content = f"\n❌ 数据库操作失败: {str(e)}"

    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=content,
    )

    return True