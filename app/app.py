import os
import random
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

@app.route("/")
def index():
    return os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == '明日の天気は？':
        weather_report(event)
    elif event.message.text == '名前は？':
        say_name(event)
    else:
        repeat_message(event)

def weather_report(event):
    list_weather = ['晴れ', '曇り', '雨', '雪', 'やばい']
    weather_index = random.randint(0, len(list_weather)-1)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="たぶん" + list_weather[weather_index] + "!"))

def say_name(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="おら、ゆうた!"))

def repeat_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))



if os.getenv('APP_ENV') == "production":
    if __name__ == '__main__':
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))