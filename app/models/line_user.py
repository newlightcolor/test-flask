from datetime import datetime
from db import db


class LineUser(db.Model):

    __tablename__ = 'line_users'

    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(255), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    pic_url = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # SELET
    def get_list(where=dict(), limit=0):
        line_users = db.session.query(LineUser)

        # WHERE
        if 'id' in where:
            line_users = line_users.filter(LineUser.id == where['id'])
        if 'line_user_id' in where:
            line_users = line_users.filter(LineUser.line_user_id == where['line_user_id'])
        if 'name' in where:
            line_users = line_users.filter(LineUser.name == where['name'])

        # 複数レコードならリスト
        if limit == 1:
            return line_users.first()
        else :
            return line_users.all()

    # INSERT
    def insert(line_user_id:str, name:str = None, pic_url:str = None):
        line_user = LineUser(line_user_id=line_user_id, name=name, pic_url=pic_url)
        db.session.add(line_user)
        db.session.commit()
        return line_user.id #insert_id

    # UPDATE
    def update(where=dict(), set=dict()):
        line_user = db.session.query(LineUser)

        # WHERE
        if 'id' in where:
            line_user = line_user.filter(LineUser.id == where['id'])
        if 'line_user_id' in where:
            line_user = line_user.filter(LineUser.line_user_id == where['line_user_id'])
        if 'latitude' in where:
            line_user = line_user.filter(LineUser.latitude == where['latitude'])
        if 'longitude' in where:
            line_user = line_user.filter(LineUser.longitude == where['longitude'])

        # SET
        line_users = line_user.all()
        for record in line_users:
            if 'name' in set:
                record.schedule=set['name']
            if 'pic_url' in set:
                record.message=set['pic_url']
            if 'latitude' in set:
                record.latitude=set['latitude']
            if 'longitude' in set:
                record.longitude=set['longitude']

        db.session.commit()