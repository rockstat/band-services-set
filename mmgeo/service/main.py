import subprocess
import os.path
import maxminddb
from band import dome, logger, RESULT_INTERNAL_ERROR, RESULT_NOT_LOADED_YET
from prodict import Prodict
"""
Library docs: https://github.com/maxmind/MaxMind-DB-Reader-python

For better performance you cat install C version of lib
https://github.com/maxmind/libmaxminddb

"""

state = Prodict(db=None)
PATH = "./data"
ARCH = f"{PATH}/a.zip"
DB = f"{PATH}/GeoLite2-City.mmdb"
DB_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz'
CMD = f'mkdir -p {PATH} && wget -q -O {ARCH} {DB_URL} && tar -zxf {ARCH} --strip=1 -C {PATH}'


@dome.tasks.add
async def download_db():
    try:
        if not os.path.isfile(DB):
            logger.info('downloading database. cmd: %s', CMD)
            out = subprocess.call(CMD, shell=True)
            logger.info('download result %s', out)
        state.db = maxminddb.open_database(DB)
    except Exception:
        logger.exception('download err')


@dome.expose(role=dome.HANDLER)
async def get(ip, **params):
    try:
        if state.db:
            location = state.db.get(ip)
            return location
        return {'result': RESULT_NOT_LOADED_YET}
    except Exception:
        logger.exception('mmgeo error')
    return {'result': RESULT_INTERNAL_ERROR}
