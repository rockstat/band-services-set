from band import dome, logger, RESULT_INTERNAL_ERROR
from pysyge.pysyge import GeoLocator, MODE_BATCH, MODE_MEMORY
from prodict import Prodict
import subprocess


state = Prodict()
DB_URL = 'http://sypexgeo.net/files/SxGeoCityMax_utf8.zip'
PATH = './data'
ARCH = f'{PATH}/sxgdb.zip'
TRG = f'{PATH}/SxGeoCity.dat'
CMD = f'mkdir -p data && wget -q -O {ARCH} {DB_URL} && unzip -o {ARCH} -d {PATH} && rm -rf {ARCH}'


@dome.tasks.add
async def startup():
    """
    Download fresh database on startup
    """
    try:
        logger.info('executing: %s', CMD)
        out = subprocess.call(CMD, shell=True)
        logger.info('download result: %s', out)
        gl = state.geodata = GeoLocator(TRG, MODE_BATCH | MODE_MEMORY)
        logger.info('DB version %s (%s)',
                    gl.get_db_version(), gl.get_db_date())
    except Exception:
        logger.exception('download err')


@dome.expose(role=dome.HANDLER)
async def get(ip, **params):
    """
    Handle incoming request
    sxg lib api details: https://github.com/idlesign/pysyge
    """
    if hasattr(state, 'geodata'):
        location = state.geodata.get_location(ip, detailed=True)
        return location
    return {'result': RESULT_INTERNAL_ERROR}
