import logging
import sqlite3
import aiohttp
import requests
from botpy.message import GroupMessage
from lxml import etree

import messageSend
from bot_qq.qqutils.ext import Command

_log = logging.getLogger(__name__)


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


@Command("查看cf用户", "mycf", "cf")
async def cf_user(message: GroupMessage, params):
    # 如果没有提供参数，尝试从数据库获取绑定的Codeforces账号
    if not params:
        # 初始化数据库连接
        messageSend.init_db()

        # 获取稳定的用户ID
        me_info = message.author.member_openid
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


@Command("绑定cf", "bindcf")
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
