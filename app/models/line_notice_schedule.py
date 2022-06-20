from datetime import datetime
from db import db


class LineNoticeSchedule(db.Model):
    __tablename__ = 'line_notice_schedule'

    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(100))
    schedule = db.Column(db.DateTime)
    message = db.Column(db.String(100), default='通知だよ～')
    finished = db.Column(db.Integer, default=0)

    #SELECT
    def get_list(where=dict(), limit=0):
        line_notice_schedule = db.session.query(LineNoticeSchedule)

        #WHERE
        if 'id' in where:
            line_notice_schedule = line_notice_schedule.filter(LineNoticeSchedule.id == where['id'])
        if 'line_user_id' in where:
            line_notice_schedule = line_notice_schedule.filter(LineNoticeSchedule.line_user_id == where['line_user_id'])
        if 'schedule' in where:
            line_notice_schedule = line_notice_schedule.filter(LineNoticeSchedule.schedule == where['schedule'])
        if 'finished' in where:
            line_notice_schedule = line_notice_schedule.filter(LineNoticeSchedule.finished == where['finished'])

        # 複数レコードなら辞書で返す
        if limit == 1:
            return line_notice_schedule.first()
        else :
            return line_notice_schedule.all()

    #INSERT
    def insert(line_user_id:str, schedule:str = None, message:str = None):
        line_notice_schedule = LineNoticeSchedule(line_user_id=line_user_id, schedule=schedule, message=message)
        db.session.add(line_notice_schedule)
        db.session.commit()
        return line_notice_schedule.id #insert_id

    #UPDATE
    def update(where=dict(), set=dict()):
        line_notice_schedule = db.session.query(LineNoticeSchedule)

        #WHERE
        if 'id' in where:
            line_notice_schedule = line_notice_schedule.filter(LineNoticeSchedule.id == where['id'])
        if 'line_user_id' in where:
            line_notice_schedule = line_notice_schedule.filter(LineNoticeSchedule.line_user_id == where['line_user_id'])
        if 'schedule' in where:
            line_notice_schedule = line_notice_schedule.filter(LineNoticeSchedule.schedule == where['schedule'])
        if 'finished' in where:
            line_notice_schedule = line_notice_schedule.filter(LineNoticeSchedule.finished == where['finished'])

        # SET
        line_notice_schedules = line_notice_schedule.all()
        for record in line_notice_schedules:
            if 'schedule' in set:
                record.schedule=set['schedule']
            if 'message' in set:
                record.message=set['message']
            if 'finished' in set:
                record.finished=set['finished']

        db.session.commit()