import os
import pprint
import random
import requests
import json
import sys
from datetime import datetime, timedelta
from dateutil import parser
from pipes import Template

from flask import Flask, request, abort, render_template
from db import init_db
from models import User, LineUser, LineNoticeSchedule
from models import SendMessageAllUserLog
from models import RakutenRecipeCategory

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate,
    PostbackEvent, QuickReply, LocationMessage, CarouselTemplate
)

from models.weather_area_code import WeatherAreaCode

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    init_db(app)

    line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
    handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

    now_average = 0
    monthly_push_message_count = 0
    for i in range(1, int(datetime.strftime(datetime.now(), ('%d')))+1):
        if len(str(i)) == 1:
            today = "0" + str(i)
        elif len(str(i)) == 2:
            today = str(i)

        if monthly_push_message_count != 0:
            now_average = monthly_push_message_count / (i-1)

        search_day = datetime.strftime(datetime.now(), ('%Y%m'))+today
        delivery_push = line_bot_api.get_message_delivery_push(date=search_day)
        if delivery_push.status == 'ready':
            monthly_push_message_count = monthly_push_message_count + delivery_push.success
        if delivery_push.status == 'unready':
            if now_average:
                monthly_push_message_count = monthly_push_message_count + now_average
    if monthly_push_message_count >= 950:
        line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN2'))
        handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET2'))

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
    @app.route("/send_message_all_user/", methods=['POST'])
    def send_message_all_user():
        # if request.form['apiKey'] != os.getenv('API_KEY'):
        #     return False

        message = request.form['message']
        SendMessageAllUserLog.insert(message=message)
        return 'OK'


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

    @app.route("/regularly_weather_report/")
    def regularly_weather_report():
        line_users = LineUser.get_list(where={'weather_area_code_not': None})
        for line_user in line_users:
            today = datetime.strftime(datetime.now(), ('%Y-%m-%d'))
            tomorrow = datetime.strftime(datetime.now() + timedelta(days=1), ('%Y-%m-%d'))
            datomorrow = datetime.strftime(datetime.now() + timedelta(days=2), ('%Y-%m-%d'))

            weather_datas = get_kishou_data(line_user.weather_area_code)
            for time, weather in weather_datas['weather'].items():
                if today in time:
                    today_weather = weather
            if today_weather[len(today_weather)-1:] == 'る':
                message = "今日は" + today_weather + "よ！\n"
            else:
                message = "今日は" + today_weather + "だよ！\n"

            for time,temp in weather_datas['temps'].items():
                if today in time:
                    if "00:00:00" in time:
                        message = message + "朝の最低気温は" + temp + "°！\n"
            for time,temp in weather_datas['temps'].items():
                if today in time:
                    if "09:00:00" in time:
                        message = message + "日中の最高気温は" + temp + "°だよ！\n"

            for time, rainchance in weather_datas['rainchances'].items():
                if today in time:
                    message = message + "【降水確率】\n"
                    break
            for time, rainchance in weather_datas['rainchances'].items():
                if today in time:
                    time = time[11:13] + "時"
                    message = message + time + "～: " + rainchance + "%\n"
            message = message[:-1]

            line_bot_api.push_message(
                line_user.line_user_id,
                TextSendMessage(text=message))

        return "とぅる～"



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
        param = postback_data_format_to_dict(event.message.text)

        if 'c' in param and 'd' in param and 'm' in param:
            # メニュー系
            if param['c'] == 'menu':
                if param['d'] == 'life':
                    if param['m'] == 'get':
                        show_life_menu(event)
                        sys.exit(0)

            # botに関すること
            if param['c'] == 'self':
                if param['d'] == 'name':
                    if param['m'] == 'get':
                        say_name(event)
                        sys.exit(0)

            # 生活関連
            if param['c'] == 'life':
                if param['d'] == 'weather':
                    if param['m'] == 'get':
                        weather_report(event)
                        sys.exit(0)
                if param['d'] == 'user':
                    if param['m'] == 'post':
                        save_user(event)
                        sys.exit(0)
                if param['d'] == 'schedule':
                    if param['m'] == 'getTemplateForSet':
                        ask_schedule(event)
                        sys.exit(0)
                if param['d'] == 'location':
                    if param['m'] == 'getQuickReplyForSet':
                        send_location_quick_reply(event)
                        sys.exit(0)
                if param['d'] == 'areaCode':
                    if param['m'] == 'post':
                        set_weather_area(event, param['select'])
                        sys.exit(0)
                if param['d'] == 'recipeCategory':
                    if param['m'] == 'get':
                        send_recipe_category(event, param['selectedCategoryId'] if 'selectedCategoryId' in param else None)
                        sys.exit(0)
                if param['d'] == 'recipe':
                    if param['m'] == 'get':
                        send_recipe(event, param['selectedCategoryId'])
                        sys.exit(0)


        # メインメニューを送信
        show_menu(event)

    # メインメニュー
    def show_menu(event):
        menu = ButtonsTemplate(
            text='何する？',
            actions=[
                {
                    'type': 'message',
                    'label': '生活メニュー',
                    'text': '&'.join(["生活メニュー見せて！\n", 'c=menu', 'd=life', 'm=get'])
                },
                {
                    'type': 'message',
                    'label': '名前は？',
                    'text': '&'.join(["名前は？\n", 'c=self', 'd=name', 'm=get'])
                }])

        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text='何する？',
                template=menu))

    # 生活メニュー
    def show_life_menu(event):
        menu = ButtonsTemplate(
            text='何する？',
            actions=[
                {
                    'type': 'message',
                    'label': '今日の天気は？',
                    'text': '&'.join(["今日の天気は？\n", 'c=life', 'd=weather', 'm=get'])
                },
                {
                    'type': 'message',
                    'label': '天気情報の地域を選択する',
                    'text': '&'.join(['c=life', 'd=areaCode', 'm=post', 'select=None'])
                },
                {
                    'type': 'message',
                    'label': '位置情報を保存する',
                    'text': '&'.join(['c=life', 'd=location', 'm=getQuickReplyForSet'])
                },
                {
                    'type': 'message',
                    'label': '通知してほしい',
                    'text': '&'.join(['c=life', 'd=schedule', 'm=getTemplateForSet'])
                }])

        line_bot_api.push_message(
            event.source.user_id,
            TemplateSendMessage(
                alt_text='何する？',
                template=menu))

        menu = ButtonsTemplate(
            text='何する？',
            actions=[
                {
                    'type': 'message',
                    'label': 'レシピ検索',
                    'text': '&'.join(["レシピ検索をしたい\n", 'c=life', 'd=recipeCategory', 'm=get'])
                }])

        line_bot_api.push_message(
            event.source.user_id,
            TemplateSendMessage(
                alt_text='何する？',
                template=menu))

    # 天気を返す
    def weather_report(event):
        line_user = LineUser.get_list(where={'line_user_id':event.source.user_id}, limit=1)
        if line_user:
            if line_user.weather_area_code:
                today = datetime.strftime(datetime.now(), ('%Y-%m-%d'))
                tomorrow = datetime.strftime(datetime.now() + timedelta(days=1), ('%Y-%m-%d'))
                datomorrow = datetime.strftime(datetime.now() + timedelta(days=2), ('%Y-%m-%d'))

                weather_datas = get_kishou_data(line_user.weather_area_code)
                for time, weather in weather_datas['weather'].items():
                    if today in time:
                        today_weather = weather
                if today_weather[len(today_weather)-1:] == 'る':
                    message = "今日は" + today_weather + "よ！\n"
                else:
                    message = "今日は" + today_weather + "だよ！\n"

                for time,temp in weather_datas['temps'].items():
                    if today in time:
                        if "00:00:00" in time:
                            message = message + "朝の最低気温は" + temp + "°！\n"
                for time,temp in weather_datas['temps'].items():
                    if today in time:
                        if "09:00:00" in time:
                            message = message + "日中の最高気温は" + temp + "°だよ！\n"

                for time, rainchance in weather_datas['rainchances'].items():
                    if today in time:
                        message = message + "【降水確率】\n"
                        break
                for time, rainchance in weather_datas['rainchances'].items():
                    if today in time:
                        time = time[11:13] + "時"
                        message = message + time + "～: " + rainchance + "%\n"
                message = message[:-1]

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=message))
            else:
                list_weather = ['晴れ', '曇り', '雨', '雪', 'やばい']
                weather_index = random.randint(0, len(list_weather)-1)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="たぶん" + list_weather[weather_index] + "!"))
        else:
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
        set_schedule_message_uri = os.getenv('BASE_URL')+'/set_schedule_message/'+line_user_id+'/'+line_notice_schedule_id+'/'

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

    # 天気情報の地域を設定
    def set_weather_area(event, select):
        if select == 'None':
            weather_area_codes = WeatherAreaCode.get_list(where={'parent_code_is_null':True})
        else:
            weather_area_codes = WeatherAreaCode.get_list(where={'parent_code':select})

        # 子地域がなければ選択肢を保存
        if len(weather_area_codes) == 0:
            area = WeatherAreaCode.get_list(where={'code':select}, limit=1)
            line_user = LineUser.get_list(where={'line_user_id':event.source.user_id}, limit=1)
            if line_user:
                LineUser.update(where={'id':line_user.id}, set={'weather_area_code':select})
            else:
                profile = line_bot_api.get_profile(event.source.user_id)
                LineUser.insert(
                    line_user_id=profile.user_id, name=profile.display_name, pic_url=profile.picture_url,
                    weather_area_code=select)
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text='天気情報の地域を'+area.name+'で保存したよ！'))
            sys.exit(0)

        # 子地域があれば送信
        actions = []
        for area in weather_area_codes:
            actions.append(
                {
                    'type': 'message',
                    'label': area.name,
                    'text': '&'.join(['c=life', 'd=areaCode', 'm=post', 'select='+area.code])
                })

            if len(actions) == 4:
                menu = ButtonsTemplate(
                    text='地域を選択してね！',
                    actions=actions)
                line_bot_api.push_message(
                    event.source.user_id,
                    TemplateSendMessage(
                        alt_text='地域を選択してね！',
                        template=menu))
                actions = []

        if actions:
            menu = ButtonsTemplate(
                text='地域を選択してね！',
                actions=actions)

            line_bot_api.push_message(
                event.source.user_id,
                TemplateSendMessage(
                    alt_text='地域を選択してね！',
                    template=menu))

    # レシピカテゴリ検索
    def send_recipe_category(event, selectedCategoryId = None):
        # 最後に選択したカテゴリのID取得
        if selectedCategoryId:
            selectedCategoryIds = selectedCategoryId.split('-')
            lastSelectedCategoryId = selectedCategoryIds[len(selectedCategoryIds)-1]
            nowLayer = len(selectedCategoryIds)
        else:
            lastSelectedCategoryId = None
            nowLayer = 0
        
        # メッセージ送信
        actions = []
        recipeCategories = RakutenRecipeCategory.get_list(where={'parent_category_id':lastSelectedCategoryId, 'layer': nowLayer+1})
        for recipeCategory in recipeCategories:
            # 選択中のIDがなければ必ずカテゴリ検索ボタン
            if selectedCategoryId:
                # 孫カテゴリが0件なら子レシピ検索ボタン
                # 孫カテゴリが1件なら孫レシピ検索ボタン
                # 孫カテゴリが1件以上ならカテゴリ検索ボタン
                childCategories = RakutenRecipeCategory.get_list(where={'parent_category_id':recipeCategory.category_id, 'layer': nowLayer+2})
                if len(childCategories) == 0:
                    actions.append({
                        'type': 'message',
                        'label': recipeCategory.category_name,
                        'text': '&'.join([recipeCategory.category_name+"\n",
                                        'c=life',
                                        'd=recipe',
                                        'm=get',
                                        'selectedCategoryId='+\
                                            '-'.join([selectedCategoryId, str(recipeCategory.category_id)])
                                        ])
                    })
                if len(childCategories) == 1:
                    actions.append({
                        'type': 'message',
                        'label': childCategories[0].category_name,
                        'text': '&'.join([childCategories[0].category_name+"\n",
                                        'c=life',
                                        'd=recipe',
                                        'm=get',
                                        'selectedCategoryId='+\
                                            '-'.join([selectedCategoryId, str(recipeCategory.category_id), str(childCategories[0].category_id)])
                                        ])
                    })
                if len(childCategories) >= 2:
                    actions.append({
                        'type': 'message',
                        'label': recipeCategory.category_name,
                        'text': '&'.join([recipeCategory.category_name+"\n",
                                        'c=life',
                                        'd=recipeCategory',
                                        'm=get',
                                        'selectedCategoryId='+selectedCategoryId+"-"+str(recipeCategory.category_id)])
                    })
            else:
                actions.append({
                    'type': 'message',
                    'label': recipeCategory.category_name,
                    'text': '&'.join([recipeCategory.category_name+"\n",
                                    'c=life',
                                    'd=recipeCategory',
                                    'm=get',
                                    'selectedCategoryId='+str(recipeCategory.category_id)])
                })

            if len(actions) >= 4:
                menu = ButtonsTemplate(text='どれがいい？',
                                        actions=actions)
                templateSendMessage = TemplateSendMessage(alt_text='どれがいい？',
                                                            template=menu)
                line_bot_api.push_message(event.source.user_id,
                                        templateSendMessage)
                actions = []

        if len(actions):
            menu = ButtonsTemplate(text='どれがいい？',
                                actions=actions)
            templateSendMessage = TemplateSendMessage(alt_text='どれがいい？',
                                                    template=menu)
            line_bot_api.push_message(event.source.user_id,
                                        templateSendMessage)
        return True

    # レシピ検索
    def send_recipe(event, selectedCategoryId):
        if selectedCategoryId:
            res = get_rakuten_recipes(selectedCategoryId)

            columns = []
            for result in res['result']:
                columns.append({
                    "thumbnailImageUrl": result['foodImageUrl'],
                    'title': result['recipeTitle'],
                    'text': result['recipeTitle'],
                    'actions': [{
                        "type": "uri",
                        "label": "このレシピを見る",
                        "uri": result['recipeUrl']
                    }]
                })
                if len(columns) >= 10:
                    carouselTemplate = CarouselTemplate(columns=columns)
                    templateSendMessage = TemplateSendMessage(alt_text="レシピ一覧",
                                                              template=carouselTemplate)
                    line_bot_api.push_message(event.source.user_id,
                                            templateSendMessage)

            if len(columns):
                carouselTemplate = CarouselTemplate(columns=columns)
                templateSendMessage = TemplateSendMessage(alt_text="レシピ一覧",
                                                          template=carouselTemplate)
                line_bot_api.push_message(event.source.user_id,
                                          templateSendMessage)
        return True


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
            if '=' in postback_data_str:
                postback_data_str = postback_data_str.split('=')
                postback_data_dict[postback_data_str[0]] = postback_data_str[1]

        return postback_data_dict



    """
    common process
    """
    def get_kishou_data(area_code):
        area = WeatherAreaCode.get_list(where={'code':area_code}, limit=1)

        # 縮小した地域レベルの復元用
        user_area_history = []
        user_area_history.append(area.code)

        # 天気情報がある地域レベルまで縮小していく
        # 地域コードの粒度に対して気象観測対象地域の粒度が大きい
        res = requests.get('https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json'.format(str(area.code)))
        request_count = 1
        while res.status_code == 404:
            area = WeatherAreaCode.get_list(
                    where={'code':area.parent_code}, limit=1)
            user_area_history.append(area.code)
            res = requests.get(
                'https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json'.format(str(area.code)))
            if request_count < 5:
                request_count = request_count+1
            if request_count >= 5:
                break

        # 複数地域のデータが帰ってくるため必要な地域のデータのみ
        if res.status_code == 200:
            res = json.loads(res.text)
            area_list = [res2.get('area') for res2 in res[0]['timeSeries'][0]['areas']]
            area_code_list = [res3.get('code') for res3 in area_list]
            for user_area in user_area_history:
                if user_area in area_code_list:
                    area_index1 = area_code_list.index(user_area)

            area_list = [res2.get('area') for res2 in res[1]['timeSeries'][0]['areas']]
            area_code_list = [res3.get('code') for res3 in area_list]
            for user_area in user_area_history:
                if user_area in area_code_list:
                    area_index2 = area_code_list.index(user_area)

            weather_datas = dict()
            weather_datas['weather'] = dict()
            for index, time in enumerate(res[0]['timeSeries'][0]['timeDefines']):
                weather_datas['weather'][datetime.strftime(parser.parse(time), ('%Y-%m-%d %H:%M:%S'))] = \
                    res[0]['timeSeries'][0]['areas'][area_index1]['weathers'][index]

            for time, weather in weather_datas['weather'].items():
                weather = weather.replace("\u3000から\u3000", 'から')
                weather = weather.replace("\u3000激しく\u3000", '激しく')
                weather = weather.replace("\u3000で\u3000", 'で、')
                weather = weather.replace("\u3000にかけて", 'にかけて')
                weather_datas['weather'][time] = weather

            weather_datas['rainchances'] = dict()
            for index, time in enumerate(res[0]['timeSeries'][1]['timeDefines']):
                weather_datas['rainchances'][datetime.strftime(parser.parse(time), ('%Y-%m-%d %H:%M:%S'))] = \
                    res[0]['timeSeries'][1]['areas'][area_index1]['pops'][index]

            weather_datas['temps'] = dict()
            for index, time in enumerate(res[0]['timeSeries'][2]['timeDefines']):
                weather_datas['temps'][datetime.strftime(parser.parse(time), ('%Y-%m-%d %H:%M:%S'))] = \
                    res[0]['timeSeries'][2]['areas'][area_index1]['temps'][index]

        return weather_datas

    def get_rakuten_recipe_categories(categoryType = None):
        if categoryType is None:
            url = "https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426"+\
                "?applicationId={applicationId}"
            url = url.format(applicationId=os.getenv('RAKUTEN_APP_ID'))
            res = requests.get(url)
            res = json.loads(res.text)
            return res['result']
        
        if categoryType:
            url = "https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426"+\
                "?format=json&categoryType={categoryType}"+\
                "&applicationId={applicationId}"
            url = url.format(categoryType=categoryType, applicationId=os.getenv('RAKUTEN_APP_ID'))
            res = requests.get(url)
            res = json.loads(res.text)
            return res['result'][categoryType]

    # 楽天レシピ取得
    def get_rakuten_recipes(recipeCategoryId):
        url = ''.join(["https://app.rakuten.co.jp/services/api/Recipe/CategoryRanking/20170426",
                       "?format={format}",
                       "&categoryId={categoryId}",
                       "&applicationId={appId}"])
        url = url.format(format='json', categoryId=recipeCategoryId, appId=os.getenv("RAKUTEN_APP_ID"))
        res = requests.get(url)
        res = json.loads(res.text)
        return res


    return app

app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)