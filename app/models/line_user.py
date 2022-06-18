from datetime import datetime
from db import db


class LineUser(db.Model):

    __tablename__ = 'line_users'

    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(100))
    name = db.Column(db.String(255))
    comment = db.Column(db.Text)
    pic_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)