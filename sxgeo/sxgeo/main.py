from band import dome, logger, settings, RESULT_INTERNAL_ERROR
from pysyge.pysyge import GeoLocator, MODE_BATCH, MODE_MEMORY
from prodict import Prodict
import subprocess
import os

state = Prodict()


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
        logger.info('DB version %s (%s)', gl.get_db_version(),
                    gl.get_db_date())
    except Exception:
        logger.exception('download err')


@dome.expose(role=dome.ENRICHER, register=dict(key=['in.gen.track']))
async def enrich(td = {}, **params):
    """
    Handle incoming request
    sxg lib api details: https://github.com/idlesign/pysyge
    """
    if hasattr(state, 'geodata'):
        location = state.geodata.get_location(td['ip'], detailed=True)
        return location
    return {'result': RESULT_INTERNAL_ERROR}
