from botpy.message import GroupMessage
from jinja2 import Environment, FileSystemLoader
from bot_qq.qqutils.ext import Command
from pygments.formatters import HtmlFormatter
from openpyxl import load_workbook

import json
import markdown
import imgkit
import requests

with open('config.json', 'r') as f:
    config = json.load(f)
    sm_ms_api_key = config[0]['PNG_API_KEY']
    API_URL = config[0]['API_URL']

env = Environment(loader=FileSystemLoader('bot_qq/templates'))
code_template = env.get_template('template.html')
echarts_template = env.get_template('echarts.html')

@Command("ai")
async def ai_command(message: GroupMessage, params):
    try:
        content = ' '.join(params)
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'text': content,
            'model': 'ernie-4.0-turbo-8k'
        }
        response = requests.post(API_URL+'/chat', json=data, headers=headers)
        decoded_response = json.loads(json.dumps(response.json()))
        result = decoded_response["response"]

        # markdown转换
        formatter = HtmlFormatter(style='monokai')  # 例如使用 Monokai 主题
        css_string = formatter.get_style_defs('.codehilite')
        html_result = f"<style>{css_string}</style>" + markdown.markdown(result,
                                                                         extensions=['fenced_code', 'codehilite',
                                                                                     'nl2br'])
        image = code_template.render(content=html_result)
        imgkit.from_string(image, 'out.jpg', options={'encoding': "UTF-8"})

        # 上传图片到 sm.ms
        try:
            headers = {
                'Authorization': sm_ms_api_key
            }
            files = {
                'smfile': ('out.jpg', open('out.jpg', 'rb'))
            }
            response = requests.post('https://sm.ms/api/v2/upload', headers=headers, files=files)
            response_json = response.json()

            # 如果上传失败
            if not response_json.get('success'):
                raise Exception(f"图片上传失败: {response_json.get('message')}")

            url = response_json['data']['url']

            # 上传成功后，发送图片
            uploadMedia = await message._api.post_group_file(
                group_openid=message.group_openid,
                file_type=1,  # 文件类型要对应上，具体支持的类型见方法说明
                url=url  # 只支持在线url
            )

            # 资源上传后，会得到 Media，用于发送消息
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=7,  # 7表示富媒体类型
                msg_id=message.id,
                media=uploadMedia
            )
            try:
                requests.get('https://sm.ms/api/v2/delete/' + response_json['data']['hash'], headers=headers)
            except Exception as e:
                print(e)

            # a1 = [f'FEATURES: {content}']
            # a2 = [f'PREDICTIONS: {result}']
            # new_training_data = [
            #     a1,
            #     a2,
            # ]
            #
            # file_path = '/root/qqbot/commands/training_data.xlsx'
            # wb = load_workbook(file_path)
            # ws = wb.active
            # for row in new_training_data:
            #     ws.append(row)
            # wb.save(file_path)
            # wb.close()

            return True
        except Exception as e:
            print(e)
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0,
                msg_id=message.id,
                content=f"\n❌ 图片上传失败 {str(e)}",
            )
            return True

    except Exception as e:
        print(e)
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_type=0,
            msg_id=message.id,
            content=f"\n❌ 查询失败 {str(e)}",
        )
        return True


@Command("mindmap")
async def mindmap_command(message: GroupMessage, params):
    try:
        content = ' '.join(params)
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'text': content,
            'model': 'ernie-4.0-turbo-8k'
        }
        response = requests.post(API_URL + '/mind_map', json=data, headers=headers)
        decoded_response = json.loads(json.dumps(response.json()))
        result = decoded_response["response"]

        # 直接将思维导图数据传给 Jinja2 模板
        image = echarts_template.render(mindmap_data=result)  # 使用 mindmap_data
        imgkit.from_string(image, 'out.jpg', options={'encoding': "UTF-8"})

        # 上传图片到 sm.ms
        try:
            headers = {
                'Authorization': sm_ms_api_key
            }
            files = {
                'smfile': ('out.jpg', open('out.jpg', 'rb'))
            }
            response = requests.post('https://sm.ms/api/v2/upload', headers=headers, files=files)
            response_json = response.json()

            # 如果上传失败
            if not response_json.get('success'):
                raise Exception(f"图片上传失败: {response_json.get('message')}")

            url = response_json['data']['url']

            # 上传成功后，发送图片
            uploadMedia = await message._api.post_group_file(
                group_openid=message.group_openid,
                file_type=1,  # 文件类型要对应上，具体支持的类型见方法说明
                url=url  # 只支持在线url
            )

            # 资源上传后，会得到 Media，用于发送消息
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=7,  # 7表示富媒体类型
                msg_id=message.id,
                media=uploadMedia
            )
            try:
                requests.get('https://sm.ms/api/v2/delete/' + response_json['data']['hash'], headers=headers)
            except Exception as e:
                print(e)
            return True

        except Exception as e:
            print(e)
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0,
                msg_id=message.id,
                content=f"\n❌ 图片上传失败 {str(e)}",
            )
            return True

    except Exception as e:
        print(e)
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_type=0,
            msg_id=message.id,
            content=f"\n❌ 查询失败 {str(e)}",
        )
        return True

