from prodict import Prodict
from band import logger
from .helpers import nn, isn, str2bool
import ujson
import asyncio
from pprint import pprint
from collections import defaultdict

from band import settings, rpc
from .band_config import BandConfig
from .docker_manager import DockerManager
from .constants import STARTED, SERVICE_TIMEOUT, DEFAULT_COL, DEFAULT_ROW
from .state_ctx import StateCtx
from .state_service import ServiceState
from .image_navigator import ImageNavigator

image_navigator = ImageNavigator(**settings)
band_config = BandConfig(**settings)
dock = DockerManager(image_navigator=image_navigator, **settings)


class StateManager:
    def __init__(self):
        self.cols = 6
        self.rows = 6
        self.timeout = 30
        self._state = dict()
        self._dock = None
        self.last_key = ''

    async def initialize(self):
        await band_config.initialize()
        await image_navigator.load()
        await self.resolve_docstatus_all()
        # check state exists
        started_present = await band_config.set_exists(STARTED)
        if not started_present:
            await band_config.set_add(STARTED, *settings.default_services)

    @property
    def state(self):
        return self._state

    def __contains__(self, name):
        return name in self._state

    async def get(self, name):
        if name not in self._state:
            logger.debug('loading state for %s', name)
            config = await band_config.load_config(name)
            meta = await image_navigator.image_meta(name)
            srv = ServiceState(name=name, manager=self)
            if meta:
                srv.set_meta(meta)

            pos_base = None
            if config:
                if 'pos' in config:
                    pos_base = config.pos

            if not pos_base and meta and nn(meta.col) and nn(meta.row):
                pos_base = dict(col=meta.col, row=meta.row)

            pos_base = pos_base or {}
            pos_base = self._allocate(name, **pos_base)
            srv.set_pos(**pos_base)
            self._state[name] = srv
        
        return self._state[name]

    async def resolve_docstatus(self, name):
        srv = await self.get(name)
        container = await dock.get(name)
        if container:
            srv.set_dockstate(container.full_state())
        

    async def resolve_docstatus_all(self):
        for container in await dock.containers(struct=list):
            await self.resolve_docstatus(container.name)

    def save_config(self, name, config):
        asyncio.ensure_future(band_config.save_config(name, config))

    def values(self):
        return self._state.values()

    def _occupied(self, exclude=None):
        """
        Building list of occupied positions
        """
        occupied = []
        for srv in self._state.values():
            if srv.name != exclude and nn(srv.pos.col) and nn(srv.pos.row):
                occupied.append(srv.pos.to_s())
        return occupied

    def _allocate(self, name, col=DEFAULT_COL, row=DEFAULT_ROW):
        """
        Allocating dashboard position for container close to wanted
        """
        logger.debug(f'{name} pos: wanted {col}x{row}')
        occupied = self._occupied(exclude=name)
        logger.debug(f'occupied positions: {occupied}')
        for icol, irow in self._space_walk(int(col), int(row)):
            logger.debug(f'> checking {icol}x{irow}')
            key = f"{icol}x{irow}"
            if key not in occupied:
                return dict(col=icol, row=irow)

    def _space_walk(self, scol=0, srow=0):
        """
        Generator over all pissible postions starting from specified location
        """
        srow = int(srow)
        scol = int(scol)
        # first part
        for rowi in range(srow, self.rows):
            for coli in range(scol, self.cols):
                yield coli, rowi
        # back side
        for rowi in range(0, srow):
            for coli in range(0, scol):
                yield coli, rowi

    async def clean_status(self, name):
        (await self.get(name)).clean_status()

    async def runned_set(self):
        return await band_config.set_get(STARTED)

    async def configs(self):
        return await band_config.configs_list()

    async def should_start(self):
        return await band_config.set_get(STARTED)

    async def add_to_startup(self, name):
        await band_config.set_add(STARTED, name)

    async def rm(self, name):
        await band_config.set_rm(STARTED, name)

    async def unload(self):
        await band_config.unload()

    def clean_ctx(self, name, coro):
        return StateCtx(self, name, coro)
