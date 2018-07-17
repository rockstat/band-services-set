from band import dome, logger, settings, RESULT_INTERNAL_ERROR
from pysyge.pysyge import GeoLocator, MODE_BATCH, MODE_MEMORY
from prodict import Prodict
import subprocess
import os
from async_lru import alru_cache

state = Prodict(geodata=None, ready=False)


@dome.tasks.add
async def startup():
    """
    Download fresh database on startup
    """
    try:
        if not os.path.isfile(settings.db_file):
            logger.info('downloading database. cmd: %s', settings.get_cmd)
            out = subprocess.call(settings.get_cmd, shell=True)
            logger.info('download result %s', out)
            out = subprocess.call(settings.extract_cmd, shell=True)
            logger.info('extract result %s', out)
        gl = state.geodata = GeoLocator(settings.db_file,
                                        MODE_BATCH | MODE_MEMORY)
        state.ready = True
        logger.info('DB version %s (%s)', gl.get_db_version(),
                    gl.get_db_date())
    except Exception:
        logger.exception('download err')


def handle_location(city=None, country=None, region=None, **kwargs):
    result = Prodict()
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


@dome.expose(role=dome.ENRICHER, keys=['in.gen.track'], props=dict(ip='td.ip'))
@alru_cache(maxsize=512)
async def enrich(ip, **params):
    if state.ready:
        try:
            if hasattr(state, 'geodata'):
                location = Prodict.from_dict(
                    state.geodata.get_location(ip, detailed=True))
                if location and location.info:
                    return handle_location(**location.info)
                return {}
            return {'result': RESULT_INTERNAL_ERROR}
        except Exception:
            logger.exception('mmgeo error')
        return {'error': RESULT_INTERNAL_ERROR}


@dome.expose()
async def cache_info():
    return enrich.cache_info()


"""
Full struct
-----------
{
    "city": "Дубна",
    "country_id": 185,
    "country_iso": "RU",
    "fips": "0",
    "info": {
        "city": {
            "id": 564719,
            "lat": 56.73333,
            "lon": 37.16667,
            "name_en": "Dubna",
            "name_ru": "Дубна"
        },
        "country": {
            "id": 185,
            "iso": "RU",
            "lat": 60.0,
            "lon": 100.0,
            "name_en": "Russia",
            "name_ru": "Россия"
        },
        "region": {
            "id": 524925,
            "iso": "RU-MOS",
            "name_en": "Moskovskaya Oblast'",
            "name_ru": "Московская область"
        }
    },
}
"""