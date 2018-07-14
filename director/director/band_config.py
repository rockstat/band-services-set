import ujson
import plyvel
import yaml
import time
import os
import aioredis
from prodict import Prodict
from band import app, settings, redis_factory, logger

def pconf(name):
    return f'band-config-{name}'


def pset(name):
    return f'band-set-{name}'


class BandConfig:
    def __init__(self, **kwargs):
        pass

    async def initialize(self):
        self.redis_pool = await redis_factory.create_pool()
        logger.debug('Band state configs holder started')

    def encode(self, **data):
        return ujson.dumps(data, ensure_ascii=False).encode()

    def decode(self, raw):
        if raw:
            return ujson.loads(raw.decode())

    async def __redis_cmd(self, cmd, *args):
        with await self.redis_pool as conn:
            return await conn.execute(cmd, *args)

    async def set_exists(self, key):
        return await self.__redis_cmd('exists', pset(key))

    async def set_add(self, key, *args):
        await self.__redis_cmd('sadd', pset(key), *args)

    async def set_rm(self, key, *args):
        await self.__redis_cmd('srem', pset(key), *args)

    async def set_get(self, key):
        return set(item.decode()
                   for item in await self.__redis_cmd('smembers', pset(key)))

    async def save_config(self, name, params):
        raw = self.encode(**params)
        with await self.redis_pool as conn:
            await conn.execute('set', pconf(name), raw)

    async def load_config(self, name):
        with await self.redis_pool as conn:
            raw = await conn.execute('get', pconf(name))
            data = self.decode(raw)
        return Prodict.from_dict(data) if isinstance(data, dict) else data

    async def unload(self):
        await redis_factory.close_pool(self.redis_pool)
