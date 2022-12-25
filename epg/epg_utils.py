import requests
from datetime import datetime
import xml.etree.ElementTree as ET


def get_url(url):
    res = requests.get(url)

    if res.status_code == 200:
        return res.text


def save_xml(data, filename='data.xml'):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)


def load_xml(filename='data.xml'):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def parse_xml(xml_data):
    return ET.fromstring(xml_data)


def get_channels_and_programmes(parsed_xml):
    channels = []
    programmes = []

    for child in parsed_xml:
        if child.tag == 'channel':
            channels.append(get_channel_data(child))

        if child.tag == 'programme':
            programmes.append(get_programme_data(child))

    sorted_programmes = sorted(programmes, key=lambda p: p['start'])
    return channels, sorted_programmes


def get_channel_data(child):
    channel_data = {'id': child.attrib['id']}
    for prop in child:
        d = _get_channel_data(prop)
        channel_data.update(d)
    return channel_data


def _get_channel_data(xml_channel_prop):
    if xml_channel_prop.tag != 'icon':
        d = {xml_channel_prop.tag: xml_channel_prop.text}
    else:
        d = {xml_channel_prop.tag: xml_channel_prop.attrib['src']}
    return d


def get_programme_data(child):
    programme_data = {
        'channel': child.attrib['channel'],
        'start': make_date(child.attrib['start']),
        'stop': make_date(child.attrib['stop'])
    }
    for prop in child:
        d = _get_programme_data(prop)
        programme_data.update(d)
    return programme_data


def make_date(date_str):
    return datetime.strptime(date_str, "%Y%m%d%H%M%S %z")


def _get_programme_data(xml_channel_prop):
    if xml_channel_prop.tag == 'credits':
        credit_data = []
        for e in xml_channel_prop:
            credit_data.append({e.tag: e.text})
        d = dict(credits=credit_data)

    elif xml_channel_prop.tag == 'desc':
        d = {xml_channel_prop.tag: xml_channel_prop.text.strip().replace('\n', '').replace('            ', ' ')}
    else:
        d = {xml_channel_prop.tag: xml_channel_prop.text}

    return d


def merge_ch_pr(channels, programmes):
    for channel in channels:
        channel['programmes'] = []
        for programme in programmes:
            if programme['channel'] == channel['id']:
                channel['programmes'].append(programme)
    return channels


def filter_chanprog(chan_prog, c_list, today_only=False):
    chann_data = [c for c in chan_prog if c['id'] in c_list]
    if today_only:
        for c in chann_data:
            c['programmes'] = [p for p in c['programmes'] if p['start'].date() == datetime.today().date()]

    return chann_data


def filter_progs(progs, c_list, today_only=False):
    programmes = [p for p in progs if p['channel'] in c_list]
    if today_only:
        programmes = [p for p in programmes if p['start'].date() == datetime.today().date()]
    return programmes
