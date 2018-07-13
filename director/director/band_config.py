import ujson
import plyvel
import yaml
import time
import os
import aioredis

from band import app, settings, redis_factory


def pref(name):
    return f'band-config-{name}'


class BandConfig:
    def __init__(self, **kwargs):
        pass

    async def startup(self, app):
        self.redis_pool = await redis_factory.create_pool()

    def encode(self, **data):
        return ujson.dumps(data, ensure_ascii=False).encode()

    def decode(self, data):
        if data:
            return ujson.loads(data.decode())

    async def save_config(self, name, params):
        raw = self.encode(**params, created_at=time.asctime())
        with await self.redis_pool as conn:
            await conn.execute('set', pref(name), raw)

    async def load_config(self, name):
        with await self.redis_pool as conn:
            raw = await conn.execute('get', pref(name))
        return self.decode(raw)

    async def unload(self, app):
        await redis_factory.close_pool(self.redis_pool)


band_config = BandConfig(**settings)
app.on_startup.append(band_config.startup)
app.on_shutdown.append(band_config.unload)
