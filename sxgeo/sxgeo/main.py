from band import expose, logger, settings, worker, response
from pysyge.pysyge import GeoLocator, MODE_BATCH, MODE_MEMORY
from prodict import Prodict as pdict
import subprocess
import os
from async_lru import alru_cache
from aiohttp.web_exceptions import HTTPInternalServerError, HTTPNoContent

state = pdict(geodata=None)


@worker()
async def startup():
    """
    Load database on startup
    """
    try:
        if not os.path.isfile(settings.db_file):
            raise FileNotFoundError("db file not found")
        state.geodata = GeoLocator(settings.db_file,
                                   MODE_BATCH | MODE_MEMORY)
        logger.info('DB version', dbver=state.geodata.get_db_version(),
                    dbdate=state.geodata.get_db_date())
    except Exception:
        logger.exception('error while opening database file')


def handle_location(city=None, country=None, region=None, **kwargs):
    result = pdict()
    if country:
        result.country_en = str(country['name_en'])
        result.country_ru = str(country['name_ru'])
        result.country_iso = str(country['iso'])
    if city:
        result.city_en = str(city['name_en'])
        result.city_ru = str(city['name_ru'])
    if region:
        result.region_en = str(region['name_en'])
        result.region_ru = str(region['name_ru'])
        result.region_iso = str(region['iso'])
    return result


@expose.enricher(keys=['in.gen.track'], props=dict(ip='td.ip'))
@alru_cache(maxsize=512)
async def enrich(**params):
    ip = params.get('ip')
    if not ip:
        return
    if state.geodata:
        try:
            location = state.geodata.get_location(ip, detailed=True)
            if location and 'info' in location:
                return handle_location(**pdict.from_dict(location['info']))
            return response.error('Database not ready')
        except Exception:
            logger.exception('mmgeo error')
            return response.error('Error while quering database')


@expose()
async def cache_info():
    return enrich.cache_info()

