import subprocess
import os.path
import aiohttp
from itertools import count, groupby
from aiohttp import ClientConnectorError
import asyncio
import aiojobs
import urllib.parse
import ujson
from prodict import Prodict
from pprint import pprint
from band import app, dome, logger, settings
from band.constants import RESULT_INTERNAL_ERROR, RESULT_NOT_LOADED_YET

from . import ch_queries

ch_dsn_parts = urllib.parse.urlparse(settings.ch_dsn)
ch_url = f"{ch_dsn_parts.scheme}://{ch_dsn_parts.hostname}:{ch_dsn_parts.port}"


async def ch_query(query):
    try:
        params = {
            'database': ch_dsn_parts.path.strip('/'),
            'user': ch_dsn_parts.username,
            'password': ch_dsn_parts.password,
            'query': query,
        }
        async with aiohttp.ClientSession() as s:
            async with s.get(ch_url, timeout=10, params=params) as r:
                if r.status == 200:
                    return await r.text()
                else:
                    logger.error(await r.text())
    except Exception:
        logger.exception('ch_query_exc')


@dome.expose()
async def web_categories(**params):
    where = ch_queries.events_where()
    query = ch_queries.groups(where)
    result = await ch_query(query + ch_queries.FMT_JSON)
    if result:
        result = ujson.loads(result)['data']
        groups = {k: list(g) for k, g in groupby(result, lambda x: x['group'])}
        return groups

