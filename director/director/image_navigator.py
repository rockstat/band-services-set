from aiofiles import os as aios
from collections import UserDict
from prodict import Prodict
from pprint import pprint
import os
import stat
import re
import subprocess

from .constants import DEF_LABELS


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

    def run_struct(self, name, img, network, memory, bind_ip, host_ports, env):
        return Prodict.from_dict({
            'Image': self.id,
            'Hostname': name,
            'Cmd': img.cmd,
            'Labels': {'inband': 'user'},
            'Env': [f"{k}={v}" for k, v in env.items()],
            'StopSignal': 'SIGTERM',
            'HostConfig': {
                'RestartPolicy': {
                    'Name': 'unless-stopped'
                },
                'PortBindings': {
                    p: [{
                        'HostIp': bind_ip,
                        'HostPort': str(hp)
                    }]
                    for hp, p in zip(host_ports, img.ports)
                },
                'NetworkMode': network,
                'Memory': memory
            }
        })

    def __enter__(self):
        self.p = subprocess.Popen(
            tar_image_cmd(self.path), stdout=subprocess.PIPE)
        return Prodict.from_dict({
            'fileobj': self.p.stdout,
            'encoding': 'identity',
            'tag': self.name,
            'labels': DEF_LABELS,
            'stream': True
        })

    def __exit__(self, exception_type, exception_value, traceback):
        self.p.kill()


def tar_image_cmd(path):
    return ['tar', '-C', path, '-c', '-X', '.dockerignore', '.']


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
        return list(self._images.values())
