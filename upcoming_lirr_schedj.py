import csv, io, os, sys, time, zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from google.transit import gtfs_realtime_pb2

STATIC_URL = 'http://web.mta.info/developers/data/lirr/google_transit.zip'
RT_URL = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/lirr%2Fgtfs-lirr'
SRC_STATION = 'Wantagh'
DST_STATION = 'Penn Station'
NY = ZoneInfo('America/New_York')
TD = gtfs_realtime_pb2.TripDescriptor


def load_static():
    resp = requests.get(STATIC_URL, timeout=30)
    resp.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(resp.content))

    def rows(name):
        with z.open(name) as f:
            yield from csv.DictReader(io.TextIOWrapper(f, 'utf-8-sig'))

    stops = {r['stop_id']: r['stop_name'] for r in rows('stops.txt')}
    trips = {r['trip_id']: r for r in rows('trips.txt')}
    return stops, trips


def fetch_feed():
    resp = requests.get(RT_URL, timeout=10)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def upcoming(feed, stop_id, trips, limit=6):
    now = time.time()
    out = []
    for entity in feed.entity:
        if not entity.HasField('trip_update'):
            continue
        tu = entity.trip_update
        # I don't think I wanna hide cancelled trains
        # if tu.trip.schedule_relationship == TD.CANCELED:
        #     continue
        for stu in tu.stop_time_update:
            if stu.stop_id != stop_id:
                continue
            ev = stu.departure if stu.HasField('departure') else stu.arrival
            if ev.time and ev.time >= now:
                trip = trips.get(tu.trip.trip_id, {})
                headsign = trip.get('trip_headsign') or tu.trip.trip_id
                out.append((ev.time, ev.delay, headsign))
    out.sort()
    return out[:limit]


if __name__ == '__main__':
    stops, trips = load_static()
    ids = [sid for sid, name in stops.items() if name == SRC_STATION ]
    if not ids:
        sys.exit(f'no stop named {SRC_STATION}; examples: {sorted(set(stops.values()))[:15]}')
    feed = fetch_feed()
    print(f'{len(feed.entity)} entities in feed')
    for t, delay, headsign in upcoming(feed, ids[0], trips):
        when = datetime.fromtimestamp(t, NY).strftime('%-I:%M %p')
        late = f' (+{delay // 60} min)' if delay >= 60 else ''
        print(f'{when}{late}  to {headsign}')