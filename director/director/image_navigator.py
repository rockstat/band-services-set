from aiofiles import os as aios
from collections import UserDict
from prodict import Prodict
from pprint import pprint
import os
import stat
import re


class ImageNavigator():
    def __init__(self, imgconfig):
        self._imgconfig = imgconfig
        self._images = {}

    async def load(self):
        for item in self._imgconfig:
            if 'collection' in item and item['collection'] == True:
                images = await self.handle_collection(**item)
                for img in images:
                    self.add_image(**img)
            else:
                self.add_image(**item)
        pprint(self._images)

    async def handle_collection(self, path, prefix, **kwargs):
        res = []
        for f in os.listdir(path):
            item = await self.check_source(os.path.join(path, f))
            if item:
                p, bn = item
                img = Prodict(name=prefix + bn, path=p)
                res.append(img)
        return res

    def add_image(self, name, path, runnable=True):
        path = os.path.realpath(path)
        self._images[name] = Prodict(name=name, path=path, runnable=runnable)

    def __getattr__(self, key):
        return self._images[key]

    def __getitem__(self, key):
        return self.images[key]

    async def check_source(self, path):
        st = await aios.stat(path)
        bn = os.path.basename(path)
        if stat.S_ISDIR(st.st_mode) and not bn.startswith('.'):
            return (path, bn)

    async def lst(self):
        res = []

        user_list = await self.lst_check_dir(self.user_path)
        res += list([(p, img_cat.user, b) for p, d, b in user_list])

        clt_list = await self.lst_check_dir(self.coll_path)
        res += list([(d, img_cat.collection, b) for p, d, b in clt_list])

        base_img = await self.check_dir(self.base_path)
        if base_img:
            p, d, b = base_img
            res.append((
                p,
                img_cat.base,
                b,
            ))

        return res
