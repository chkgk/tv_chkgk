from flask import Flask, render_template, make_response, request, redirect
from datetime import datetime, timedelta
from collections import OrderedDict

import pytz
import os
import json
from epg.epg_utils import load_xml, get_url, save_xml, parse_xml, get_channels_and_programmes, merge_ch_pr


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship


db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tv.sqlite"
db.init_app(app)


class Channels(db.Model):
    __tablename__ = 'Channels'
    id = Column(String(64), primary_key=True)
    display_name = Column(String(128))
    icon = Column(String(256))
    url = Column(String(256))

    programmes = relationship('Programmes', back_populates='channel')


class Programmes(db.Model):
    __tablename__ = 'Programmes'
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(64), ForeignKey('Channels.id'))
    channel = relationship('Channels', back_populates='programmes')

    start = Column(DateTime)
    stop = Column(DateTime)
    title = Column(String(256))
    sub_title = Column(String(256))
    desc = Column(Text)


def query_database(channels=[], date=None):
    if not date:
        date = datetime.today().date()
    if not channels:
        channels = ('DasErste.de', 'ZDF.de', 'RTLGermany.de', 'SAT1.de', 'ProSieben.de')
    return db.session.query(Programmes) \
        .filter(Programmes.channel_id.in_(channels), func.DATE(Programmes.start) == date).all()


def prepare_data(query_result):
    start_times = dict()
    channels = set()
    smallest_delta = None
    smallest_delta_time = '00:00'
    now = pytz.utc.localize(datetime.utcnow())

    for d in query_result:
        channels.add((d.channel_id, d.channel.display_name))

        d.start = pytz.utc.localize(d.start)
        delta = abs(now - d.start)
        t_start = d.start.astimezone(pytz.timezone('CET')).strftime('%H:%M')
        if not smallest_delta:
            smallest_delta = delta
            smallest_delta_time = t_start
        if delta < smallest_delta:
            smallest_delta = delta
            smallest_delta_time = t_start

        if t_start in start_times:
            start_times[t_start].append(d)
        else:
            start_times[t_start] = [d]

    sorted_start_times = OrderedDict(sorted(start_times.items()))

    res = OrderedDict()
    ids, names = zip(*channels)
    for time, lis in sorted_start_times.items():
        res[time] = {
            'channels': names,
            'programmes': []
        }
        clist = [None for _ in ids]
        for i, c in enumerate(ids):
            for p in lis:
                if p.channel_id == c:
                    clist[i] = p
            res[time]['programmes'] = clist

    return res, names, smallest_delta_time


@app.route('/')
def index():
    cookie_channels = json.loads(request.cookies.get('channels', '[]'))
    data = query_database(channels=cookie_channels)
    prepared_data, names, delta = prepare_data(data)
    return render_template('index.htm', context=prepared_data, channels=names, date=datetime.today().date(), anchor=delta)


@app.route('/settings', methods=['POST', 'GET'])
def settings():
    if request.method == 'GET':
        cookie_channels = json.loads(request.cookies.get('channels', '[]'))
        channels = db.session.query(Channels).all()
        return render_template('settings.htm', channels=channels, selected=cookie_channels)

    if request.method == 'POST':
        channels = request.form.getlist('channels')
        resp = make_response(redirect('/'))
        resp.set_cookie('channels', json.dumps(channels))
        return resp


if __name__ == '__main__':
    app.run()
