import subprocess
import os.path
import maxminddb
from band import expose, worker, logger, settings, response
from prodict import Prodict as pdict
from async_lru import alru_cache
from aiohttp.web_exceptions import HTTPServiceUnavailable
from transliterate import translit

state = pdict(db=None)


@worker()
async def open_db():
    try:
        if not os.path.isfile(settings.db_file):
            raise FileNotFoundError("db file not found")
        state.db = maxminddb.open_database(settings.db_file)
        logger.info('DB loaded')
    except Exception:
        logger.exception('error while opening database file')


@expose()
async def cache_info():
    return enrich.cache_info()


@expose.enricher(keys=['in.gen.track'], props=dict(ip='td.ip'))
@alru_cache(maxsize=512)
async def enrich(ip, **params):
    try:
        if state.db:
            location = state.db.get(ip)
            if location:
                return handle_location(**location)
            return {}
        raise HTTPServiceUnavailable()
    except Exception:
        logger.exception('mmgeo error.', location=location)
        return response.error()


def handle_location(city=None, country=None, subdivisions=None, **kwargs):
    result = pdict()
    if country:
        result.country_en = country['names']['en']
        result.country_ru = country['names']['ru']
        result.country_iso = country['iso_code']
    if city and 'names' in city:
        result.city_en = city['names']['en']
        result.city_ru = (city['names']['ru']
                          if 'ru' in city['names'] else en_to_ru(
                              city['names']['en']))
    if subdivisions and len(subdivisions) > 0:
        region = subdivisions[0]
        result.region_en = region['names']['en']
        result.region_ru = (region['names']['ru']
                            if 'ru' in region['names'] else en_to_ru(
                                region['names']['en']))
        result.region_iso = region['iso_code']
    return result


def en_to_ru(text):
    return translit(text, 'ru')
