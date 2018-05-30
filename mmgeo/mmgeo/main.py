import subprocess
import os.path
import maxminddb
from band import dome, logger, settings, RESULT_INTERNAL_ERROR, RESULT_NOT_LOADED_YET
from prodict import Prodict
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
