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

    def get_list(where=dict(), limit=0):
        line_users = LineUser

        if 'id' in where:
            line_users = line_users.query.filter(line_users.id == where['id'])
        if 'line_user_id' in where:
            line_users = line_users.query.filter(line_users.line_user_id == where['line_user_id'])
        if 'name' in where:
            line_users = line_users.query.filter(line_users.name == where['name'])

        # 複数レコードなら辞書で返す
        if limit == 1:
            return line_users.first()
        else :
            return line_users.all()