from aiofiles import os as aios
from collections import UserDict
from prodict import Prodict
from pprint import pprint
import os
import stat
from .band_image import BandImage


"""
Takes list of images and collections descriptions and builds dictionary of each image ready to build.
Config example:
    images:
    - name: rst/band-base
        path: "{{BASE_IMG_PATH|default(IMAGES_PATH+'/band_base')}}"
    - prefix: rst/band-
        collection: true
        base: rst/band-base
        path: "{{IMAGES_PATH}}/band_collection"
    - prefix: rst/user-
        collection: true
        path: "{{IMAGES_PATH}}/user"
"""


class ImageNavigator():
    def __init__(self, imgconfig):
        self._imgconfig = imgconfig
        self._images = {}

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __getitem__(self, key):
        return self._images[key]

    async def load(self):
        self._images = {}
        for item in self._imgconfig:
            item = {**item}
            collection = item.pop('collection', None)
            if collection == True:
                images = await self.handle_collection(**item)
                for img in images:
                    self.add_image(**img)
            else:
                self.add_image(**item)

    async def handle_collection(self, **kwargs):
        prefix = kwargs.pop('prefix')
        path = kwargs.pop('path')
        res = []
        for d in os.listdir(path):
            item = await self.check_source(os.path.join(path, d))
            if item:
                p, bn = item
                img = dict(name=prefix + bn, path=p, key=d, **kwargs)
                res.append(img)
        return res

    def add_image(self, name, path, **kwargs):
        path = os.path.realpath(path)
        key = kwargs.pop('key', None)
        img = BandImage(name=name, path=path, key=key, **kwargs)
        self._images[name] = img
        if key:
            self._images[key] = img

    async def check_source(self, path):
        st = await aios.stat(path)
        bn = os.path.basename(path)
        if stat.S_ISDIR(st.st_mode) and not bn.startswith('.'):
            return (path, bn)

    async def lst(self):
        await self.load()
        # handle hidden images, and base without key
        return list(
            i for k, i in self._images.items() if i.name == k and i.key)
