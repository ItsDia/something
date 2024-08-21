from botpy.message import GroupMessage
from zhipuai import ZhipuAI
from jinja2 import Environment, FileSystemLoader
from bot_qq.qqutils.ext import Command
from pygments.formatters import HtmlFormatter

import json
import markdown
import imgkit
import requests

with open('config.json', 'r') as f:
    config = json.load(f)
    client = ZhipuAI(api_key=config[0]['API_KEY'])
    sm_ms_api_key = config[0]['PNG_API_KEY']

env = Environment(loader=FileSystemLoader('bot_qq/templates'))
code_template = env.get_template('template.html')


@Command("ai")
async def ai_command(message: GroupMessage, params):
    try:
        content = ' '.join(params)
        response = client.chat.completions.create(
            model="codegeex-4",
            messages=[
                {
                    "role": "system",
                    "content": "你是一位智能编程助手，你叫CodeGeeX。你会为用户回答关于编程、代码、计算机方面的任何问题，并提供 'Markdown格式的规范、可以执行、准确安全、换行标准的代码'注意代码本身不能和markdown语法冲突，如果冲突请解决，而且markdown的文字颜色为'白色'或者其他不与黑色背景冲突的颜色,代码块的背景颜色设置成黑色,并在必要时提供详细的解释。任务：请为输入代码提供格式规范的注释，包含多行注释和单行注释，请注意不要改动原始代码，只需要添加注释。 请用中文回答，并且代码注意换行，代码默认使用C语言或者C++语言，记得给用户标注是用的什么语言。"

                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            top_p=0.7,
            temperature=0.9,
            max_tokens=1024,
            stop=["<|endoftext|>", "<|user|>", "<|assistant|>", "<|observation|>"],
            do_sample=False
        )
        result = response.choices[0].message.content

        # markdown转换
        formatter = HtmlFormatter(style='monokai')  # 例如使用 Monokai 主题
        css_string = formatter.get_style_defs('.codehilite')
        html_result = f"<style>{css_string}</style>" + markdown.markdown(result, extensions=['fenced_code', 'codehilite', 'nl2br'])
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

        except Exception as e:
            print(e)
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0,
                msg_id=message.id,
                content=f"\n❌ 图片上传失败 {str(e)}",
            )
            return True

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