from datetime import datetime
from db import db


class WeatherAreaCode(db.Model):

    __tablename__ = 'weather_area_code'

    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(20), nullable=True)
    code = db.Column(db.String(20), nullable=True)
    parent_code = db.Column(db.String(20), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    en_name = db.Column(db.String(100), nullable=True)
    office = db.Column(db.String(100), nullable=True)

    # SELET
    def get_list(where=dict(), limit=0):
        areas = db.session.query(WeatherAreaCode)

        # WHERE
        if 'id' in where:
            areas = areas.filter(WeatherAreaCode.id == where['id'])
        if 'section' in where:
            areas = areas.filter(WeatherAreaCode.section == where['section'])
        if 'code' in where:
            areas = areas.filter(WeatherAreaCode.code == where['code'])
        if 'parent_code' in where:
            areas = areas.filter(WeatherAreaCode.parent_code == where['parent_code'])
        if 'parent_code_is_null' in where:
            areas = areas.filter(WeatherAreaCode.parent_code == None)
        if 'name' in where:
            areas = areas.filter(WeatherAreaCode.name == where['name'])
        if 'en_name' in where:
            areas = areas.filter(WeatherAreaCode.en_name == where['en_name'])
        if 'office' in where:
            areas = areas.filter(WeatherAreaCode.office == where['office'])

        # 複数レコードならリスト
        if limit == 1:
            return areas.first()
        else :
            return areas.all()

    # INSERT
    def insert(section:str, code:str, name:str, parent_code:str = None, en_name:str = None, office:str = None):
        area = \
            WeatherAreaCode(section=section, code=code, name=name, parent_code=parent_code, en_name=en_name, office=office)
        db.session.add(area)
        db.session.commit()
        return area.id #insert_id
