from pathlib import Path
from collections import namedtuple
import aiofiles
import asyncio
import aiodocker
import os
import stat
import re
from prodict import Prodict
from time import time
import ujson
import subprocess
from pprint import pprint
from band import logger
from .image_navigator import ImageNavigator
from .band_container import BandContainer
from .constants import DEF_LABELS, STATUS_RUNNING


class DockerManager():
    """
    Useful links:
    http://aiodocker.readthedocs.io/en/latest/
    https://docs.docker.com/engine/api/v1.37/#operation/ContainerList
    https://docs.docker.com/engine/api/v1.24/#31-containers
    """

    def __init__(self,
                 images,
                 container_params,
                 start_port=8900,
                 end_port=8999,
                 **kwargs):
        self.dc = aiodocker.Docker()
        self.start_port = start_port
        self.end_port = end_port
        self.imgnav = ImageNavigator(images)
        self.container_params = Prodict.from_dict(container_params)

    async def init(self):
        await self.imgnav.load()
        conts = await self.containers()
        for cont in conts.values():
            logger.info(
                f"inspecting container {cont.name}. inband: {cont.inband()}  -> port:{cont.ports}"
            )
        return [cont.short_info for cont in conts.values()]

    async def containers(self, struct=dict, status=None):
        filters = Prodict(label=['inband'])
        if status:
            filters.status = [status]
        conts = await self.dc.containers.list(
            all=True, filters=ujson.dumps(filters))
        lst = list(bc for bc in [BandContainer(c) for c in conts])
        return lst if struct == list else {c.name: c for c in lst}

    async def conts_list(self):
        conts = await self.containers()
        return [c.short_info for c in conts.values()]

    async def get(self, name):
        c = (await self.containers()).get(name, None)
        return c and c.data

    async def available_ports(self):
        available_ports = set(range(self.start_port, self.end_port))
        conts = await self.containers()
        used_ports = set(sum(list(cont.ports for cont in conts.values()), []))
        logger.info(f"checking used ports {used_ports}")
        return available_ports - used_ports

    async def remove_container(self, name):
        await self.stop_container(name)
        conts = await self.containers()
        if name in list(conts.keys()):
            logger.info(f"removing container {name}")
            await conts[name].delete()
        return True

    async def stop_container(self, name):
        conts = await self.containers()
        if name in conts:
            logger.info(f"stopping container {name}")
            await conts[name].stop()
            return True

    async def restart_container(self, name):
        conts = await self.containers()
        if name in conts:
            logger.info(f"restarting container {name}")
            await conts[name].restart()
            return True

    async def create_image(self, img):
        logger.info(f"building image {img.name} from {img.path}")
        new_id = 0
        with img as struct:
            progress = Prodict()
            last = time()
            async for chunk in await self.dc.images.build(**struct):
                if isinstance(chunk, dict):
                    chunk = Prodict.from_dict(chunk)
                    if chunk.aux:
                        struct.id = chunk.aux.ID
                    elif chunk.status and chunk.id:
                        progress[chunk.id] = chunk
                        if time() - last > 2:
                            logger.info("\n%s", progress)
                            last = time()
                    # elif chunk.stream:
                    #     step = re.search(r'Step\s(\d+)\/(\d+)', chunk.stream)
                    #     if step:
                    #         logger.debug('Step %s [%s]', *step.groups())
                    else:     
                        logger.debug('%s', chunk)
                else:
                    logger.debug('chunk: %s %s', type(chunk), chunk)
            logger.info('image created %s', struct.id)
            return img.set_data(await self.dc.images.get(struct.id))

    async def run_container(self, name, params):
        simg = self.imgnav[name]
        # rebuild base image
        # if simg.base:
            # await self.create_image(self.imgnav[simg.base])
        img = await self.create_image(simg)
        available_ports = await self.available_ports()
        params = {
            'host_ports': list(available_ports.pop() for p in img.ports),
            **self.container_params
        }
        config = img.run_struct(name, img, **params)
        logger.info(f"starting container {name}.")
        c = BandContainer(await self.dc.containers.create_or_replace(
            name, config))
        await c.start()
        logger.info(f'started container {c.name} [{c.short_id}] {c.ports}')
        return c.short_info

    async def close(self):
        await self.dc.close()
