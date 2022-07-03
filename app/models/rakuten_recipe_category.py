from datetime import datetime
from db import db


class RakutenRecipeCategory(db.Model):
    __tablename__ = 'rakuten_recipe_category'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, nullable=False)
    parent_category_id = db.Column(db.Integer, nullable=True)
    category_name = db.Column(db.String(100), nullable=True)
    category_url = db.Column(db.String(200), nullable=True)

    #SELECT
    def get_list(where=dict(), limit=0):
        rakuten_recipe_category = db.session.query(RakutenRecipeCategory)

        #WHERE
        if 'id' in where:
            rakuten_recipe_category = rakuten_recipe_category.filter(RakutenRecipeCategory.id == where['id'])
        if 'parent_category_id' in where:
            rakuten_recipe_category = rakuten_recipe_category.filter(RakutenRecipeCategory.parent_category_id == where['parent_category_id'])
        if 'category_id' in where:
            rakuten_recipe_category = rakuten_recipe_category.filter(RakutenRecipeCategory.category_id == where['caetogry_id'])

        # 複数レコードなら辞書で返す
        if limit == 1:
            return rakuten_recipe_category.first()
        else :
            return rakuten_recipe_category.all()

    #INSERT
    def insert(category_id:int, parent_category_id:int = None, category_name:str = None, category_url:str = None):
        rakuten_recipe_category = RakutenRecipeCategory(
                                                    category_id=category_id,
                                                    parent_category_id=parent_category_id,
                                                    category_name=category_name,
                                                    category_url=category_url)
        db.session.add(rakuten_recipe_category)
        db.session.commit()
        return rakuten_recipe_category.id #insert_id

    #UPDATE
    def update(where=dict(), set=dict()):
        rakuten_recipe_category = db.session.query(RakutenRecipeCategory)

        #WHERE
        if 'id' in where:
            rakuten_recipe_category = rakuten_recipe_category.filter(RakutenRecipeCategory.id == where['id'])

        # SET
        rakuten_recipe_categorys = rakuten_recipe_category.all()
        for record in rakuten_recipe_categorys:
            if 'schedule' in set:
                record.schedule=set['schedule']

        db.session.commit()