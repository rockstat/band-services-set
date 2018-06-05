from aiofiles import os as aios
from collections import UserDict
from prodict import Prodict
from pprint import pprint
import os
import stat
import re
import subprocess

from .constants import DEF_LABELS
from .helpers import tar_image_cmd


class BandImageBuilder:
    def __init__(self, img, img_options):
        self.img = img
        self.img_options = img_options

    async def __aenter__(self):
        self.p = subprocess.Popen(
            tar_image_cmd(self.img.path), stdout=subprocess.PIPE)
        return self

    def struct(self):
        return Prodict.from_dict({
            'fileobj': self.p.stdout,
            'encoding': 'identity',
            'tag': self.img.name,
            'nocache': self.img_options.get('nocache', False),
            'pull': self.img_options.get('pull', False),
            'labels': DEF_LABELS,
            'stream': True
        })

    async def __aexit__(self, exception_type, exception_value, traceback):
        self.p.kill()

class BandImage(Prodict):
    name: str
    path: str
    key: str
    base: str
    p: subprocess.Popen
    d: Prodict

    def set_data(self, data):
        self.d = Prodict.from_dict(data)
        return self

    @property
    def cmd(self):
        return self.d.Config.Cmd

    @property
    def id(self):
        return self.d.Id

    @property
    def ports(self):
        return list(self.d.ContainerConfig.ExposedPorts.keys())

    def create(self, img_options):
        return BandImageBuilder(self, img_options)

    def run_struct(self, name, network, memory, bind_ip, host_ports, auto_remove, env, **kwargs):
        return Prodict.from_dict({
            'Image': self.id,
            'Hostname': name,
            'Cmd': self.cmd,
            'Labels': {
                'inband': 'user'
            },
            'Env': [f"{k}={v}" for k, v in env.items()],
            'StopSignal': 'SIGTERM',
            'HostConfig': {
                'AutoRemove': auto_remove,
                # 'RestartPolicy': {'Name': 'unless-stopped'},
                'PortBindings': {
                    p: [{
                        'HostIp': bind_ip,
                        'HostPort': str(hp)
                    }]
                    for hp, p in zip(host_ports, self.ports)
                },
                'NetworkMode': network,
                'Memory': memory
            }
        })



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
