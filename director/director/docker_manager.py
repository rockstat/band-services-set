from pathlib import Path
from collections import namedtuple
import aiofiles
import asyncio
import aiodocker
from aiodocker.exceptions import DockerError
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
from .helpers import str2bool

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
        asyncio.ensure_future(self.imgnav.load())
        self.container_params = Prodict.from_dict(container_params)

    async def init(self):
        await self.imgnav.load()

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
        return (await self.containers()).get(name, None)

    async def available_ports(self):
        available_ports = set(range(self.start_port, self.end_port))
        conts = await self.containers()
        used_ports = set(sum(list(cont.ports for cont in conts.values()), []))
        logger.info(f"checking used ports {used_ports}")
        return available_ports - used_ports

    async def remove_container(self, name):
        # removing if running
        try:
            container = await self.get(name)
            if container:
                await container.fill()
                if container.state == 'running':
                    logger.info("Stopping container")
                    await container.stop()
                    if not container.d.HostConfig.AutoRemove:
                        await container.delete()
                else:
                    await container.delete()
                await container.wait(condition="removed")
                
        except DockerError:
            logger.exception('container remove exc')
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

    async def create_image(self, img, img_options):
        logger.debug(
            f">>> Building image {img.name} from {img.path}. img_options: %s",
            img_options)
        async with img.create(img_options) as builder:
            progress = Prodict()
            struct = builder.struct()
            last = time()
            async for chunk in await self.dc.images.build(**struct):
                if isinstance(chunk, dict):
                    chunk = Prodict.from_dict(chunk)
                    if chunk.aux:
                        struct.id = chunk.aux.ID
                        logger.debug('%s', chunk)
                    elif chunk.status and chunk.id:
                        progress[chunk.id] = chunk
                        if time() - last > 1:
                            logger.info("\n%s", progress)
                            last = time()
                    elif chunk.stream:
                        # logger.debug('%s', chunk)
                        step = re.search(r'Step\s(\d+)\/(\d+)', chunk.stream)
                        if step:
                            logger.debug('Step %s [%s]', *step.groups())
                    else:
                        logger.debug('%s', chunk)
                else:
                    logger.debug('chunk: %s %s', type(chunk), chunk)
            logger.info('image created %s', struct.id)
            return img.set_data(await self.dc.images.get(img.name))

    async def run_container(self, name, env={}, nocache='no', auto_remove='yes', **kwargs):
        img_options = dict(nocache=str2bool(nocache))
        cont_options = dict(auto_remove=str2bool(auto_remove))
        service_img = self.imgnav[name]
        # rebuild base image
        if service_img.base:
            base_img = self.imgnav[service_img.base]
            await self.create_image(base_img, img_options)
        #creating service image
        await self.create_image(service_img, img_options)
        
        await self.remove_container(name)
        await asyncio.sleep(1)
        # preparing to build
        available_ports = await self.available_ports()
        params = Prodict.from_dict({
            'host_ports':
            list(available_ports.pop() for p in service_img.ports),
            **self.container_params
        })
        params.env.update(env)
        config = service_img.run_struct(name, **cont_options, **params)
        logger.info(f"starting container {name}.")
        dc = await self.dc.containers.run(config=config, name=name)
        c = BandContainer(dc)
        await c.ensure_filled()
        logger.info(f'started container {c.name} [{c.short_id}] {c.ports}')
        return c.short_info

    async def close(self):
        await self.dc.close()
