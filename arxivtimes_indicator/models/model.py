from collections import defaultdict, Counter
from datetime import datetime

import dateutil.parser
import dateutil.relativedelta
from peewee import *


db = SqliteDatabase('my_app.db')


def create_tables():
    if not Issue.table_exists():
        db.create_table(Issue)
    if not Label.table_exists():
        db.create_table(Label)


def drop_tables():
    if Issue.table_exists():
        Issue.drop_table()
    if Label.table_exists():
        Label.drop_table()


class BaseModel(Model):
    class Meta:
        database = db


class Issue(BaseModel):
    title = CharField()
    url = CharField(primary_key=True, unique=True)
    user_id = CharField()
    avatar_url = CharField()
    score = IntegerField()
    created_at = DateTimeField()
    body = TextField()

    def extract_headline(self):
        headline_left = len('## 一言でいうと')
        headline_right = self.body.index('###')  # until next section
        headline = self.body[headline_left:headline_right].strip()

        return headline


class Label(BaseModel):
    issue = ForeignKeyField(Issue, to_field='url', related_name='labels')
    name = CharField()

    def __init__(self, name):  # Aggregate label names
        super(Label, self).__init__()
        self.name = name


def get_recent(user_id, limit):
    if user_id:
        return Issue.select().where(Issue.user_id==user_id).order_by(Issue.created_at).limit(limit)
    else:
        return Issue.select().order_by(Issue.created_at).limit(limit)


def get_popular(user_id, limit):
    if user_id:
        return Issue.select().where(Issue.user_id == user_id).order_by(Issue.score).limit(limit)
    else:
        return Issue.select().order_by(Issue.score).limit(limit)


def aggregate_per_month(user_id="", month=6, use_genre=True):
    now = datetime.now()
    start_time = now - dateutil.relativedelta.relativedelta(months=month)
    start_time_str = start_time.strftime("%Y-%m-01 00:00:00+00:00")
    if user_id:
        issues = Issue.select().where(Issue.user_id == user_id).where(Issue.created_at >= start_time_str)
    else:
        issues = Issue.select().where(Issue.created_at >= start_time_str)
    counter = defaultdict(Counter)
    for issue in issues:
        key = dateutil.parser.parse(issue.created_at).strftime('%Y/%m')
        for label in issue.labels:
            counter[key][label] += 1
    return counter


def aggregate_kinds(user_id="", month=6, use_genre=True):
    counters = aggregate_per_month(user_id, month, use_genre)
    counter = Counter()
    for c in counters.values():
        counter += c
    return counter