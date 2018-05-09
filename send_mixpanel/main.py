import subprocess
import os.path
import asyncio
import aiohttp
import base64
from time import time
from itertools import zip_longest
import ujson as json
import urllib
from band import dome, logger, settings, app

"""
Mixpanel exporter.

docs:
https://mixpanel.com/help/reference/http
https://docs.aiohttp.org/en/stable/client.html
"""


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def flatten_dict(dd, separator='_', prefix=''):
    return {prefix + separator + k if prefix else k: v
            for kk, vv in dd.items()
            for k, v in flatten_dict(vv, separator, kk).items()
            } if isinstance(dd, dict) else {prefix: dd}


class State(dict):
    def __init__(self):
        self.buffer = []

    def add_item(self, item):

        flat = flatten_dict(item)
        flat['distinct_id'] = flat.get('uid', None)
        flat['token'] = settings.mixpanel_token
        flat['time'] = round(time())
        ev = {
            'event': flat.get('name', 'unknown'),
            'properties': flat
        }
        self.buffer.append(ev)

    def grab(self):
        batch = self.buffer
        self.buffer = []
        return batch


state = State()
MP_TRACK_EP = 'http://api.mixpanel.com/track/'


@dome.expose(role=dome.LISTENER)
async def listener(**params):
    state.add_item(params)


@dome.tasks.add
async def download_db():
    while True:
        try:
            await app['rpool'].subscribe(app['mpsc'].channel('any'))
            logger.info('subscribed any')
            async with aiohttp.ClientSession() as session:
                while True:
                    batch = state.grab()
                    if len(batch):
                        enc = json.dumps(batch, ensure_ascii=False)
                        q = urllib.parse.urlencode(
                            {'data': base64.encodebytes(enc.encode())})
                        async with session.post(MP_TRACK_EP, data=q) as resp:
                            logger.info('uploading %s items. code %s',
                                        len(batch), resp.status)
                    await asyncio.sleep(1)
            pass
        except Exception:
            logger.exception('err - root loop')
