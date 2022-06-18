from datetime import datetime
from db import db


class LineNoticeSchedule(db.Model):
    __tablename__ = 'line_notice_schedule'

    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(100))
    schedule = db.Column(db.DateTime)
    message = db.Column(db.String(100), default='通知だよ～')
    finished = db.Column(db.Integer, default=0)