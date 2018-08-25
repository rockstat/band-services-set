from prodict import Prodict as pdict
from typing import List, Dict
from time import time
from random import randint
from collections import deque
from .constants import SERVICE_TIMEOUT, STATUS_RUNNING, STATUS_STARTING, STATUS_REMOVING
from .helpers import nn, isn, str2bool
from band import logger, app


class MethodRegistration(pdict):
    method: str
    role: str
    options: Dict


class ServiceDashPosition(pdict):
    col: int
    row: int

    def is_filled(self):
        return nn(self.col) and nn(self.row)

    def to_s(self):
        if self.is_filled():
            return f"{self.col}x{self.row}"


class ServiceState(pdict):
    _meta: pdict
    _app: pdict
    _app_ts: int
    _dock: pdict
    _dock_ts: int
    _pos: ServiceDashPosition
    _build_options: pdict
    _methods: List[MethodRegistration]
    _name: str
    _title: str
    _managed: bool
    _protected: bool
    _persistent: bool
    _native: bool

    def __init__(self, manager, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pos = ServiceDashPosition()
        self._manager = manager
        self._build_options = pdict()
        self._env = pdict()
        self._logs = deque(maxlen=1000)
        self._name = name
        self._title = name.replace('_', ' ').title()
        self.clean_status()
            

    def clean_status(self):
        logger.debug('restoring state of %s', self.name)
        self._meta = pdict()
        self._app = pdict()
        self._app_ts = None
        self._methods = []
        self._status_override = None
        self._dock = pdict()
        self._dock_ts = None
        self._methods = []
        self._managed = False
        self._protected = False
        self._persistent = False
        self._native = False

    @property
    def config(self):
        return pdict(
            pos=self.pos, build_options=self.build_options, env=self._env)

    def full_state(self):
        docker = self.dockstate
        appdata = self.appstate
        state = None
        running = None
        uptime = None
        inband = False
        if docker:
            running = docker.running
            state = docker.state
            inband = docker.inband
            if appdata and appdata.app_uptime:
                uptime = appdata.app_uptime
            else:
                uptime = docker.uptime
        elif appdata and appdata.app_state == STATUS_RUNNING:
            running = True
            state = STATUS_RUNNING
            uptime = appdata.app_uptime

        return pdict(
            name=self.name,
            uptime=uptime,
            state=self._status_override or state,
            title=self.title,
            inband=inband,
            pos=self.pos,
            # TODO: remove when dashboard updated
            sla=randint(98, 99),
            mem=randint(1, 3),
            cpu=randint(1, 3),
            stat=dict(
                sla=randint(98, 99),
                mem=randint(1, 3),
                cpu=randint(1, 3),
            ),
            meta=dict(
                native=self._native,
                managed=self._managed,
                protected=self._protected,
                persistent=self._persistent))

    @property
    def methods(self):
        return self._methods

    @property
    def pos(self):
        return self._pos

    def set_title(self, title):
        self._title = title

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def native(self):
        return self._native

    def is_active(self):
        ds = self.dockstate
        if ds and ds.state == STATUS_RUNNING:
            return True
        else:
            ass = self.appstate
            if ass and ass.app_state == STATUS_RUNNING:
                return True
        return False

    @property
    def build_options(self):
        return self._build_options

    def set_build_opts(self, **params):
        # old env location. moving to root location
        if 'env' in params:
            self.set_env(params.pop('env', {}))

        self._build_options.update(params)

    @property
    def env(self):
        return self._env

    def set_env(self, env):
        self._env = env

    def set_pos(self, col, row):
        if nn(col) and nn(row):
            self._pos.col = col
            self._pos.row = row

    @property
    def meta(self):
        return self._meta

    def set_meta(self, meta):
        if not meta:
            return
        self._meta = meta
        if 'title' in meta:
            self.set_title(meta.title)

    def save_config(self):
        self._manager.save_config(self.name, self.config)

    @property
    def appstate(self):
        if self._app_ts and time() < self._app_ts + SERVICE_TIMEOUT:
            return self._app

    def set_status_override(self, status):
        self._status_override = status

    def set_status_starting(self):
        self._status_override = STATUS_STARTING
        pass

    def set_status_removing(self):
        self._status_override = STATUS_REMOVING
        pass

    def set_methods(self, methods):
        if not methods: return
        self._methods = []
        for method in methods:
            rec = method.copy()
            rec.update(service=self.name)
            self._methods.append(rec)

    def set_appstate(self, appstate):
        if appstate:
            self._app = appstate
            self._app_ts = time()
            if 'register' in appstate:
                self.set_methods(appstate['register'])

    @property
    def dockstate(self):
        if self._dock_ts and time() < self._dock_ts + SERVICE_TIMEOUT:
            return self._dock

    def set_dockstate(self, dockstate):
        if dockstate:
            self._dock = dockstate
            self._managed = True
            self._status_override = None
            if self.meta:
                if nn(self.meta.protected):
                    self._protected = self.meta.protected
                if nn(self.meta.persistent):
                    self._persistent = self.meta.persistent
                if nn(self.meta.native):
                    self._native = self.meta.native

            if dockstate.running == True:
                self._dock_ts = time()
