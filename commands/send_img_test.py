from botpy.message import GroupMessage

from bot_qq.qqutils.ext import Command


@Command("test")
async def on_group_at_message_create(message: GroupMessage, params):
    file_url = "https://s2.loli.net/2024/08/08/4mtKeNZlTQX8u2v.gif"  # 这里需要填写上传的资源Url
    uploadMedia = await message._api.post_group_file(
        group_openid=message.group_openid,
        file_type=1,  # 文件类型要对应上，具体支持的类型见方法说明
        url=file_url  # 只支持在线url
    )

    # 资源上传后，会得到Media，用于发送消息
    await message._api.post_group_message(
        group_openid=message.group_openid,
        msg_type=7,  # 7表示富媒体类型
        msg_id=message.id,
        media=uploadMedia
    )

    return True
