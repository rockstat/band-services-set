import subprocess
import os.path
import maxminddb
from band import dome, logger, settings, RESULT_INTERNAL_ERROR, RESULT_NOT_LOADED_YET
from prodict import Prodict
from async_lru import alru_cache
from aiohttp.web_exceptions import HTTPServiceUnavailable
"""
Library docs: https://github.com/maxmind/MaxMind-DB-Reader-python

For better performance you cat install C version of lib
https://github.com/maxmind/libmaxminddb
"""

class MMGState(Prodict):
    db: object
    ready: bool

state = MMGState(db=None, ready=False)


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
        state.ready = True
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


@dome.expose(role=dome.ENRICHER, keys=['in.gen.track'], props=dict(ip='td.ip'))
@alru_cache(maxsize=512)
async def enrich(ip, **params):
    try:
        if state.ready == True and state.db:
            location = state.db.get(ip)
            if location:
                return handle_location(**location)
            return {}
        raise HTTPServiceUnavailable('Database not ready yet')
    except Exception:
        logger.exception('mmgeo error. location: %s', location)
    return {'error': RESULT_INTERNAL_ERROR}


@dome.expose()
async def cache_info():
    return enrich.cache_info()


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