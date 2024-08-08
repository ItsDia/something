import logging
import random
import sqlite3
from datetime import datetime

from botpy.message import GroupMessage

import messageSend
from bot_qq.qqutils.ext import Command

_log = logging.getLogger(__name__)

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