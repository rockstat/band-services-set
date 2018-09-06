import subprocess
import os.path
import asyncio
import aiohttp
import base64
from time import time
import ujson
import urllib
from band import dome, logger, settings, app
from prodict import Prodict
from typing import List
"""
Mixpanel exporter.

docs:
https://mixpanel.com/help/reference/http
https://docs.aiohttp.org/en/stable/client.html

"""


def flatten_dict(dd, separator=settings.separator, prefix=''):
    return {
        prefix + separator + k if prefix else k: v
        for kk, vv in dd.items()
        for k, v in flatten_dict(vv, separator, kk).items()
    } if isinstance(dd, dict) else {
        prefix: dd
    }


def prefixer(dd, prefix=settings.prefix):
    return {prefix + k: v
            for k, v in dd.items()} if isinstance(dd, dict) else {
                prefix: dd
    }


class CopyClear:
    def __init__(self, item):
        self.item = item

    def __enter__(self):
        return self.item[:]

    def __exit__(self, exc_type, exc, tb):
        self.item.clear()


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


@dome.expose(role=dome.LISTENER)
async def broadcast(**params):
    state.add_item(params)


@dome.tasks.add
async def uploader():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
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
