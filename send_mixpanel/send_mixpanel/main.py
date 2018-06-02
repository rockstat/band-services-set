import subprocess
import os.path
import asyncio
import aiohttp
import base64
from time import time
import ujson as json
import urllib
from band import dome, logger, settings, app
from prodict import Prodict
from typing import List
"""
Mixpanel exporter.

docs:
https://mixpanel.com/help/reference/http
https://docs.aiohttp.org/en/stable/client.html

[01:12:42] DEBUG Creating tcp connection to ('host.docker.internal', 6379)
[01:12:42] DEBUG Connection has been closed by server, response: None
[01:12:42] INFO redis_rpc_reader: entering loop
[01:12:42] DEBUG Creating tcp connection to ('host.docker.internal', 6379)


"""


def flatten_dict(dd, separator='_', prefix=''):
    return {
        prefix + separator + k if prefix else k: v
        for kk, vv in dd.items()
        for k, v in flatten_dict(vv, separator, kk).items()
    } if isinstance(dd, dict) else {
        prefix: dd
    }


class State(dict):
    def __init__(self):
        self.buffer = []

    def add_item(self, item):
        flat = flatten_dict(item)
        flat.update({
            'distinct_id': flat.get('uid', None),
            'token': settings.mixpanel_token,
            'time': round(time())
        })
        self.buffer.append({
            'event': flat.get('name', 'unknown'),
            'properties': flat
        })

    def grab(self):
        buff = self.buffer[:]
        self.buffer.clear()
        return buff


state = State()
MP_ENDPOING = 'http://api.mixpanel.com/track/'


@dome.expose(role=dome.LISTENER)
async def listener(**params):
    state.add_item(params)


@dome.tasks.add
async def uploader():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    batch = state.grab()
                    if len(batch):
                        enc = json.dumps(batch, ensure_ascii=False)
                        q = urllib.parse.urlencode({
                            'data':
                            base64.encodebytes(enc.encode())
                        })
                        async with session.post(MP_ENDPOING, data=q) as resp:
                            logger.info('uploading %s items. Status: %s',
                                        len(batch), resp.status)
                    await asyncio.sleep(1)
            pass
        except Exception:
            logger.exception('mp upload')


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)
