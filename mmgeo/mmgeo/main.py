import subprocess
import os.path
import maxminddb
from band import dome, logger, settings, RESULT_INTERNAL_ERROR, RESULT_NOT_LOADED_YET
from prodict import Prodict
from async_lru import alru_cache
"""
Library docs: https://github.com/maxmind/MaxMind-DB-Reader-python

For better performance you cat install C version of lib
https://github.com/maxmind/libmaxminddb
"""

state = Prodict(db=None)


@dome.tasks.add
async def download_db():
    try:
        if not os.path.isfile(settings.db_file):
            logger.info('downloading database. cmd: %s', settings.get_cmd)
            out = subprocess.call(settings.get_cmd, shell=True)
            logger.info('download result %s', out)
            out = subprocess.call(settings.extract_cmd, shell=True)
            logger.info('extract result %s', out)
        state.db = maxminddb.open_database(settings.db_file)
    except Exception:
        logger.exception('download err')


def handle_location(city=None, country=None, subdivisions=None, **kwargs):
    result = Prodict()
    if country:
        result.country_en = country['names']['en']
        result.country_ru = country['names']['ru']
        result.country_iso = country['iso_code']
    if city:
        result.city_en = city['names']['en']
        result.city_ru = city['names']['ru']
    if subdivisions and len(subdivisions) > 0:
        region = subdivisions[0]
        result.region_en = region['names']['en']
        result.region_ru = region['names']['ru']
        result.region_iso = region['iso_code']
    return result


@alru_cache(maxsize=256)
async def locate(ip):
    try:
        if state.db:
            location = state.db.get(ip)
            return handle_location(**location)
        return {'error': RESULT_NOT_LOADED_YET}
    except Exception:
        logger.exception('mmgeo error')
    return {'error': RESULT_INTERNAL_ERROR}


@dome.expose(
    role=dome.ENRICHER,
    register=dict(key=['in.gen.track'], props=dict(ip='td.ip')))
async def enrich(td, **params):
    return await locate(td['ip'])


@dome.expose()
async def cache_info():
    return locate.cache_info()


@dome.expose()
async def get(ip, **params):
    return await locate(ip)


"""
Full struct
-----------
{
    "city": {
        "geoname_id": 524901,
        "names": {
            "de": "Moskau",
            "en": "Moscow",
            "es": "Moscú",
            "fr": "Moscou",
            "ja": "モスクワ",
            "pt-BR": "Moscovo",
            "ru": "Москва",
            "zh-CN": "莫斯科"
        }
    },
    "continent": {
        "code": "EU",
        "geoname_id": 6255148,
        "names": {
            "de": "Europa",
            "en": "Europe",
            "es": "Europa",
            "fr": "Europe",
            "ja": "ヨーロッパ",
            "pt-BR": "Europa",
            "ru": "Европа",
            "zh-CN": "欧洲"
        }
    },
    "country": {
        "geoname_id": 2017370,
        "iso_code": "RU",
        "names": {
            "de": "Russland",
            "en": "Russia",
            "es": "Rusia",
            "fr": "Russie",
            "ja": "ロシア",
            "pt-BR": "Rússia",
            "ru": "Россия",
            "zh-CN": "俄罗斯"
        }
    },
    "location": {
        "accuracy_radius": 1000,
        "latitude": 55.7522,
        "longitude": 37.6156,
        "time_zone": "Europe/Moscow"
    },
    "postal": {
        "code": "102617"
    },
    "registered_country": {
        "geoname_id": 2017370,
        "iso_code": "RU",
        "names": {
            "de": "Russland",
            "en": "Russia",
            "es": "Rusia",
            "fr": "Russie",
            "ja": "ロシア",
            "pt-BR": "Rússia",
            "ru": "Россия",
            "zh-CN": "俄罗斯"
        }
    },
    "subdivisions": [
        {
            "geoname_id": 524894,
            "iso_code": "MOW",
            "names": {
                "de": "Moskau",
                "en": "Moscow",
                "es": "Moscú",
                "fr": "Moscou",
                "ru": "Москва"
            }
        }
    ]
}
"""