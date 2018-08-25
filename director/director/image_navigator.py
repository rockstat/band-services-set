import aiofiles
import yaml
import stat
import os
from aiofiles import os as aios
from collections import UserDict
from prodict import Prodict as pdict
from .band_image import BandImage


class ImageNavigator():
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

    def __init__(self, images, *args, **kwargs):
        self._imgconfig = images
        self._images = {}

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __getitem__(self, key):
        return self._images.get(key, None)

    def __contains__(self, key):
        return key in self._images

    def is_native(self, name):
        return name in self._images

    async def load(self):
        self._images = {}
        for item in self._imgconfig:
            item = {**item}
            collection = item.pop('collection', None)
            if collection == True:
                for img in await self.__handle_collection(**item):
                    await self.__add_image(**img)
            else:
                await self.__add_image(**item)


    async def image_meta(self, name):
        if name in self._images:
            return self[name].get('meta', None)

    async def __handle_collection(self, **kwargs):
        prefix = kwargs.pop('prefix')
        path = kwargs.pop('path')
        res = []
        for d in os.listdir(path):
            item = await self.__check_source(os.path.join(path, d))
            if item:
                p, bn = item
                img = dict(name=prefix + bn, path=p, key=d, **kwargs)
                res.append(img)
        return res

    async def __read_meta(self, path):
        meta_config_path = f"{path}/meta.yml"
        meta = dict(native=True)
        if os.path.exists(meta_config_path) and os.path.isfile(
                meta_config_path):
            async with aiofiles.open(meta_config_path, mode='r') as f:
                contents = await f.read()
                meta.update(yaml.load(contents))
        return meta

    async def __add_image(self, name, path, **kwargs):
        path = os.path.realpath(path)
        meta = await self.__read_meta(path)
        key = kwargs.pop('key', None)
        img = BandImage(name=name, path=path, key=key, meta=meta, **kwargs)
        self._images[name] = img
        if key:
            self._images[key] = img

    async def __check_source(self, path):
        st = await aios.stat(path)
        bn = os.path.basename(path)
        if stat.S_ISDIR(st.st_mode):
            if not bn.startswith('__') and not bn.startswith('.'):
                return (path, bn)

    async def lst(self):
        await self.load()
        # handle hidden images, and base without key
        return list(
            i for k, i in self._images.items() if i.name == k and i.key)
