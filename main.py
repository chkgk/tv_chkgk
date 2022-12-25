import os
from epg.epg_utils import load_xml, get_url, save_xml, parse_xml, get_channels_and_programmes, merge_ch_pr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app import Channels, Programmes
from datetime import datetime
from json import loads


def load_config(filename='config.json'):
    with open(filename, 'r', encoding='utf-8') as f:
        return loads(f.read())


def replace_data(dbs, channels_programms):
    # clean up
    dbs.query(Programmes).delete()
    dbs.query(Channels).delete()
    dbs.commit()

    for channel in channels_programms:
        chan_obj = dbs.query(Channels.id) \
            .filter_by(id=channel['id']) \
            .first()

        if not chan_obj:
            chan_obj = Channels(
                id=channel['id'],
                display_name=channel['display-name'],
                icon=channel['icon'],
                url=channel['url']
            )
            dbs.add(chan_obj)
            # print('added:', channel['id'])
        else:
            print('!! exists:', channel['id'])

        for prog in channel['programmes']:
            prog_obj = dbs.query(Programmes.title) \
                .filter_by(channel_id=chan_obj.id, start=prog['start']) \
                .first()

            if not prog_obj:
                prog_obj = Programmes(
                    channel_id=chan_obj.id,
                    start=prog['start'],
                    stop=prog['stop'],
                    title=prog['title'],
                    sub_title=prog.get('sub-title', None),
                    desc=prog.get('desc', None)
                )
                dbs.add(prog_obj)
                # print('added:', prog['title'])
            else:
                print('!! exists:', prog['title'])

    dbs.commit()


def main():
    engine = create_engine('sqlite:///instance/tv.sqlite')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    config = load_config()

    filename = f"tv-data-{datetime.today().date()}.xml"
    path = os.path.join('data', filename)

    if not os.path.exists(path):
        data = get_url(config['epg-url'])
        save_xml(data, path)

    file_content = load_xml(path)
    parsed = parse_xml(file_content)

    channels, programmes = get_channels_and_programmes(parsed)
    channels_with_programmes = merge_ch_pr(channels, programmes)
    replace_data(session, channels_with_programmes)
    print('done')


if __name__ == '__main__':
    main()
