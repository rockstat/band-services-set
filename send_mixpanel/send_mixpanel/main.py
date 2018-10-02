import subprocess
import asyncio
from aiohttp import ClientSession
import base64
from time import time
import ujson
import urllib
from band import logger, settings, expose, worker

from .helpers import CopyClear, flatten_dict, prefixer


class State(dict):
    def __init__(self):
        self.buffer = []

    def add_item(self, item):
        flat_data = flatten_dict(item.pop('data', {}))
        masked = prefixer(item)
        flat_data.update(masked)
        flat_data.update({
            'distinct_id': item.get('uid', None),
            'token': settings.mixpanel_token,
            'time': round(time())
        })
        mp_rec = {
            'event':
            item.get('service', 'none') + '/' + item.get('name', 'none'),
            'properties': flat_data
        }
        self.buffer.append(mp_rec)

    def grab(self):
        with CopyClear(self.buffer) as buff:
            return buff


state = State()


@expose.listener()
async def broadcast(**params):
    state.add_item(params)


@worker()
async def uploader():
    while True:
        try:
            async with ClientSession() as session:
                while True:
                    batch = state.grab()
                    if len(batch):
                        enc = ujson.dumps(batch, ensure_ascii=False)
                        q = urllib.parse.urlencode({
                            'data':
                            base64.encodebytes(enc.encode())
                        })
                        async with session.post(
                                settings.endpoint, data=q) as resp:
                            logger.info('uploading', items=len(
                                batch), status=resp.status)
                    await asyncio.sleep(1)
            pass
        except asyncio.CancelledError:
            logger.info('cancelled')
            break
        except Exception:
            logger.exception('upload')
