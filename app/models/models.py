from datetime import datetime
from db import db


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

class LineUser(db.Model):

    __tablename__ = 'line_users'

    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(100))
    name = db.Column(db.String(255))
    comment = db.Column(db.Text)
    pic_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

class LineNoticeSchedule(db.Model):
    __tablename__ = 'line_notice_schedule'

    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(100))
    schedule = db.Column(db.DateTime)
    message = db.Column(db.String(100), default='通知だよ～')
    finished = db.Column(db.Integer, default=0)