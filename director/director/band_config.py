import ujson
import plyvel
import yaml
import time
import os


class BandConfig:
    def __init__(self, data_dir, **kwargs):
        self.db = plyvel.DB(f'{data_dir}/db', create_if_missing=True)

    def encode(self, **data):
        return ujson.dumps(data, ensure_ascii=False).encode()

    def decode(self, data):
        if data:
            return ujson.loads(data.decode())

    def save_config(self, name, params):
        raw = self.encode(**params, created_at=time.asctime())
        self.db.put(name.encode(), raw)

    def load_config(self, name):
        raw = self.db.get(name.encode())
        return self.decode(raw)

    def unload(self):
        self.db.close()
