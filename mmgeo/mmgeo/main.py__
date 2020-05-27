import subprocess
import os.path
import maxminddb
import asyncio
from band import expose, worker, logger, settings, response
from prodict import Prodict as pdict
from async_lru import alru_cache
from aiohttp.web_exceptions import HTTPServiceUnavailable
from itertools import count
from transliterate import translit

state = pdict(db=None)



@expose()
async def cache_info():
    return dict(enrich.cache_info()._asdict())


@expose.enricher(keys=[settings.key_prefix], props=settings.props)
@alru_cache(maxsize=512)
async def enrich(**params):
    try:
        ip = params.get('ip', None)
        if not state.db:
            raise HTTPServiceUnavailable()
        if ip:
            location = state.db.get(ip)
            if location:
                return handle_location(**location)
        return {}
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
        result.city_ru = (city['names']['ru'] if 'ru' in city['names'] else
                          en_to_ru(city['names']['en']))
    if subdivisions and len(subdivisions) > 0:
        region = subdivisions[0]
        result.region_en = region['names']['en']
        result.region_ru = (region['names']['ru'] if 'ru' in region['names']
                            else en_to_ru(region['names']['en']))
        result.region_iso = region['iso_code']
    return result


def en_to_ru(text):
    return translit(text, 'ru')


@worker()
async def loader():
    try:
        if not os.path.isfile(settings.db_file):
            raise FileNotFoundError("db file not found")
        state.db = maxminddb.open_database(settings.db_file)
        logger.info('DB loaded')

        for num in count():
            info = await cache_info()
            logger.info('cache stat', loop=num, info=info)
            await asyncio.sleep(60 * 5)
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception('error while opening database file')

