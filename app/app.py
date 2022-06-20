import os
import pprint
import random
from datetime import datetime
from pipes import Template

from flask import Flask, request, abort, render_template
from db import init_db
from models import User, LineUser, LineNoticeSchedule

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate,
    PostbackEvent, QuickReply, LocationMessage
)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    init_db(app)

    line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
    handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

    """
    WebAPP route
    """
    @app.route("/")
    def index():
        return "test-"

    @app.route("/set_schedule_message/<line_user_id>/<schedule_id>/")
    def set_schedule_message(line_user_id=None, schedule_id=None):
        return render_template('set_schedule_message.html',
                                line_user_id=line_user_id,
                                schedule_id=schedule_id)

    @app.route("/set_schedule_message_finish/", methods=['POST'])
    def set_schedule_message_finish():
        id = request.form['schedule_id']
        line_user_id = request.form['line_user_id']
        schedule = LineNoticeSchedule.get_list(where={'id':id, 'line_user_id':line_user_id}, limit=1)

        message = request.form['schedule_message']
        if schedule is None:
            error_message='この予定は存在しないみたい...'
            return render_template('error.html', error_message=error_message)
        elif message == '':
            error_message='メッセージが入力されてないよ！'
            return render_template('error.html', error_message=error_message)
        else :
            LineNoticeSchedule.update(where={'id':id}, set={'message':message})
            success_message='「' + message + '」で通知するね！'
            success_title='OK!'
            return render_template('success.html', success_message=success_message, success_title=success_title)



    """
    API route
    """



    """
    CRON route
    """
    @app.route("/notice_schedule/")
    def notice_schedule():
        schedules_send_notify = LineNoticeSchedule.get_list(where={'schedule_lte': datetime.now()})
        for schedule in schedules_send_notify:
            line_bot_api.push_message(
                schedule.line_user_id,
                TextSendMessage(text="通知だよ！:\n" + schedule.message)
            )
        return 'とぅる～'


    """
    line callback
    """
    # LineAPIサーバーに返すだけ
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



    """
    text message action handle
    """
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        if event.message.text == '明日の天気は？':
            weather_report(event)
        elif event.message.text == '名前は？':
            say_name(event)
        elif event.message.text == '記録':
            save_user(event)
        elif event.message.text == '位置情報を保存':
            send_location_quick_reply(event)
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
                    'label': '位置情報を保存',
                    'text': '位置情報を保存'
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

        insert_id = LineUser.insert(name=profile.display_name, line_user_id=line_user_id, pic_url=profile.picture_url)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="記録したよ～"))

    # 位置情報クイックリプライを送信
    def send_location_quick_reply(event):
        line_user_id = event.source.user_id
        profile = line_bot_api.get_profile(line_user_id)
        insert_id = LineUser.insert(name=profile.display_name, line_user_id=line_user_id, pic_url=profile.picture_url)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="位置情報を入力してね！",
                quick_reply=QuickReply(items=[
                                                {
                                                    'type': 'action',
                                                    'action':
                                                    {
                                                        'type': 'location',
                                                        'label': '位置情報を入力'
                                                    }
                                                }
                                            ])
            ))

    # スケジュールを尋ねる
    def ask_schedule(event):
        line_user_id = event.source.user_id
        line_notice_schedule_id = str(LineNoticeSchedule.insert(line_user_id=line_user_id))
        set_schedule_message_uri = 'https://flask-linebot300995.herokuapp.com/set_schedule_message/'+\
                                    line_user_id+'/'+line_notice_schedule_id+'/'

        buttonsTemplate = ButtonsTemplate(
            text='いつ通知すればいい？',
            actions=[
                {
                    'type': 'datetimepicker',
                    'label': '日付を入力',
                    'data': 'action=line_notice_schedule&how=set_datetime&line_notice_schedule_id='+line_notice_schedule_id,
                    'mode': 'datetime',
                },
                {
                    'type': 'uri',
                    'label': '通知内容を入力',
                    'uri': set_schedule_message_uri
                },
                {
                    'type': 'postback',
                    'label': 'やっぱいいや',
                    'data': 'action=line_notice_schedule&how=cancel&line_notice_schedule_id='+line_notice_schedule_id
                }])

        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text='いつ通知すればいい？',
                template=buttonsTemplate))



    """
    location message action handle
    """
    @handler.add(MessageEvent, message=LocationMessage)
    def handle_message(event):
        save_location(event)

    # 位置情報をユーザー情報に記録
    def save_location(event):
        line_users = LineUser.get_list(where={'line_user_id':event.source.user_id})
        if line_users:
            line_user = line_users[0]
            LineUser.update(
                where={'id':line_user.id},
                set={'latitude': event.message.latitude, 'longitude': event.message.longitude})
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(
                    text='Latitude:'+str(event.message.latitude)+' Longitude:'+str(event.message.longitude)+' で更新したよ！'))
        else :
            profile = line_bot_api.get_profile(event.source['user_id'])
            LineUser.insert(
                line_user_id=profile.user_id, name=profile.display_name,
                pic_url=profile.picture_url, latitude=event.message.latitude, longitude=event.message.longitude)
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(
                    text='Latitude:'+str(event.message.latitude)+' Longitude:'+str(event.message.longitude)+' で保存したよ！'))



    """
    postback action handle
    """
    @handler.add(PostbackEvent)
    def on_postback(event):
        # データを辞書に変換
        postback_data = postback_data_format_to_dict(event.postback.data)

        # 通知スケジュールの変更
        if postback_data['action'] == 'line_notice_schedule':
            if postback_data['how'] == 'set_datetime':
                LineNoticeSchedule.update(
                    where={'id':postback_data['line_notice_schedule_id']},
                    set={'schedule':event.postback.params['datetime']})
                line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(text='OK! ' + event.postback.params['datetime'] + 'ね！')
                )
            if postback_data['how'] == 'cancel':
                line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(text='そんな～😭')
                )

    # postbackデータを文字列から辞書に変換
    def postback_data_format_to_dict(postback_data):
        # データリスト文字列を個別データ文字列にリスト化
        postback_data_str_list = [data.strip() for data in postback_data.split('&')]

        # 個別データ文字列をリストに変化
        postback_data_dict = dict()
        for postback_data_str in postback_data_str_list:
            postback_data_str = postback_data_str.split('=')
            postback_data_dict[postback_data_str[0]] = postback_data_str[1]

        return postback_data_dict



    return app

app = create_app()