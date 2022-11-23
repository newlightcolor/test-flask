from datetime import datetime
from db import db
from sqlalchemy.dialects import mysql


class SendMessageAllUserLog(db.Model):

    __tablename__ = 'send_message_all_user_log'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    create_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # SELET
    def get_list(where=dict(), limit=0):
        query = db.session.query(SendMessageAllUserLog)

        # WHERE
        if 'id' in where:
            query = query.filter(SendMessageAllUserLog.id == where['id'])

        # 複数レコードならリスト
        if limit == 1:
            return query.first()
        else :
            return query.all()

    # INSERT
    def insert(message:str):
        query = \
            SendMessageAllUserLog(message=message)
        db.session.add(query)
        db.session.commit()
        return query.id #insert_id
