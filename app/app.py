import os
import pprint
from pipes import Template
import random

from flask import Flask, request, abort
from db import init_db, db
from models import User, LineUser, LineNoticeSchedule

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackEvent
)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    init_db(app)

    line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
    handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

    @app.route("/")
    def index():
        return "test-"

    @app.route("/push_message/<message>")
    def push_message(message):
        return "pushed message"

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
        elif event.message.text == '記録':
            save_user(event)
        elif event.message.text == '予定':
            ask_schedule(event)
        else:
            show_menu(event)

    # できること一覧
    def show_menu(event):
        menu = ButtonsTemplate(
            text='何する？',
            actions=[
                {
                    'type': 'message',
                    'label': '明日の天気は？',
                    'text': '明日の天気は？'
                },
                {
                    'type': 'message',
                    'label': '名前は？',
                    'text': '名前は？'
                },
                {
                    'type': 'message',
                    'label': '記録',
                    'text': '記録'
                },
                {
                    'type': 'message',
                    'label': '予定',
                    'text': '予定'
                }])

        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text='何する？',
                template=menu))

    # 適当に天気を返す
    def weather_report(event):
        list_weather = ['晴れ', '曇り', '雨', '雪', 'やばい']
        weather_index = random.randint(0, len(list_weather)-1)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="たぶん" + list_weather[weather_index] + "!"))

    # 自己紹介
    def say_name(event):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="おら、ゆうた!"))

    # ユーザーを登録
    def save_user(event):
        line_user_id = event.source.user_id
        profile = line_bot_api.get_profile(line_user_id)

        line_user = LineUser(name=profile.display_name, line_user_id=line_user_id, pic_url=profile.picture_url)
        db.session.add(line_user)
        db.session.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="記録したよ～"))

    # スケジュールを尋ねる
    def ask_schedule(event):
        buttonsTemplate = ButtonsTemplate(
            text='いつ通知すればいい？',
            actions=[
                {
                    'type': 'datetimepicker',
                    'label': '日付を入力',
                    'data': 'action=datetemp&selectId=1',
                    'mode': 'datetime',
                },
                {
                    'type': 'uri',
                    'label': '通知内容を入力',
                    'uri': 'https://www.youtube.com/watch?v=5qap5aO4i9A&ab_channel=LofiGirl'
                },
                {
                    'type': 'postback',
                    'label': 'やっぱいいや',
                    'data': 'action=cancel&selectId=2'
                }])

        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text='いつ通知すればいい？',
                template=buttonsTemplate))

    def repeat_message(event):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))

    @handler.add(PostbackEvent)
    def on_postback(event):
        user_id = event.source.user_id
        postback_msg = event.postback.data
        postback_params = event.postback.params
        pprint.pprint(event.postback)

        if postback_msg == 'action=datetemp&selectId=1':
            line_notice_schedule = LineNoticeSchedule(
                line_user_id=user_id,
                schedule=postback_params['datetime']
            )
            db.session.add(line_notice_schedule)
            db.session.commit()

            message = 'OK! ' + postback_params['datetime'] + 'ね！'
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=message)
            )
        elif postback_msg == 'action=cancel&selectId=2':
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text='そんな～😭')
            )



    return app

app = create_app()