from prodict import Prodict
from typing import List, Dict
from time import time
from random import randint
from .constants import SERVICE_TIMEOUT, STATUS_RUNNING
from .helpers import nn, isn, str2bool


class MethodRegistration(Prodict):
    method: str
    role: str
    options: Dict


class ServiceDashPosition(Prodict):
    col: int
    row: int

    def is_filled(self):
        return nn(self.col) and nn(self.row)

    def to_s(self):
        if self.is_filled():
            return f"{self.col}x{self.row}"


class ServiceState(Prodict):
    _app: Prodict
    _app_ts: int
    _dock: Prodict
    _dock_ts: int
    _pos: ServiceDashPosition
    _build_options: Prodict
    _methods: List[MethodRegistration]
    _name: str
    _title: str

    def __init__(self, manager, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = Prodict()
        self._dock = Prodict()
        self._pos = ServiceDashPosition()
        self._methods = []
        self._build_options = Prodict()
        self._manager = manager

        self._name = name
        self._title = name.replace('_', ' ').title()

    def clean_status(self):
        self._app = Prodict()
        self._app_ts = None
        self._dock = Prodict()
        self._dock_ts = None
        self._methods = []

    @property
    def config(self):
        return Prodict(pos=self.pos, build_options=self.build_options)

    def full_state(self):
        ds = self.dockstate
        ass = self.appstate
        state = None
        running = None
        uptime = None
        if ds:
            running = ds.running
            state = ds.state
            if ass and ass.app_uptime:
                uptime = ass.app_uptime
            else:
                uptime = ds.uptime
        elif ass and ass.app_state == STATUS_RUNNING:
            running = True
            state = STATUS_RUNNING
            uptime = ass.app_uptime        
        return Prodict(
            name=self.name,
            uptime=uptime,
            state=state,
            running=running,
            title=self.title,
            pos=self.pos,
            sla=randint(98, 99),
            mem=randint(1, 3),
            cpu=randint(1, 3),
        )

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

    def set_build_opts(self, **kwargs):
        if 'env' in kwargs:
            self._build_options.update(env=kwargs['env'])
        if 'nocache' in kwargs:
            self._build_options.update(nocache=str2bool(kwargs['nocache']))
        if 'auto_remove' in kwargs:
            self._build_options.update(auto_remove=str2bool(kwargs['auto_remove']))

    def set_pos(self, col, row):
        if nn(col) and nn(row):
            self._pos.col = col
            self._pos.row = row

    def set_meta(self, meta):
        if meta:
            if 'title' in meta:
                self.set_title(meta.title)

    def save_config(self):
        self._manager.save_config(self.name, self.config)

    @property
    def appstate(self):
        if self._app_ts and time() < self._app_ts + SERVICE_TIMEOUT:    
            return self._app

    def set_appstate(self, appstate):
        if appstate:
            self._app = appstate
            self._app_ts = time()
            self.save_config()
            if 'register' in appstate:
                self._methods = []
                for method in appstate['register']:
                    rec = method.copy()
                    rec.update(service=self.name)
                    self._methods.append(rec)
    @property
    def dockstate(self):
        if self._dock_ts and time() < self._dock_ts + SERVICE_TIMEOUT:    
            return self._dock


    def set_dockstate(self, dockstate):
        if dockstate:
            self._dock = dockstate
            if dockstate.running == True:
                self.save_config()
                self._dock_ts = time()
