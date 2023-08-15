from datetime import datetime
from peewee import Model, SqliteDatabase, TextField, IntegerField, DateTimeField, CharField, ForeignKeyField


db = SqliteDatabase('database.db')


class _BaseModel(Model):
    class Meta:
        database = db


class ReferralLink(_BaseModel):
    class Meta:
        db_table = 'referral_links'

    name = CharField(unique=True)
    user_count = IntegerField(default=0)
    passed_op_count = IntegerField(default=0)


class Movie(_BaseModel):
    class Meta:
        db_table = 'movie'

    code = IntegerField(unique=True)
    title = TextField()
    description = TextField(default=None)
    photo_id = CharField(default=None, null=True)
    url = CharField(default=None)


class User(_BaseModel):
    class Meta:
        db_table = 'users'

    name = CharField(default='Пользователь')
    telegram_id = IntegerField(unique=True, null=False)
    registration_timestamp = DateTimeField()
    referral_link = CharField(null=True)


class Admin(_BaseModel):
    class Meta:
        db_table = 'admins'

    telegram_id = IntegerField(unique=True, null=False)
    name = CharField()


class Favorite(_BaseModel):
    user = ForeignKeyField(User, backref='favorites')
    movie = ForeignKeyField(Movie, backref='favorites')


class Channel(_BaseModel):
    class Meta:
        db_table = 'channels'

    channel_id = IntegerField()
    title = CharField()
    url = CharField()


def register_models() -> None:
    for model in _BaseModel.__subclasses__():
        model.create_table()
