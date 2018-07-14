from prodict import Prodict
from time import time
from band import logger
from .helpers import nn, isn, str2bool
from typing import List, Dict
import ujson
from pprint import pprint
from collections import defaultdict
from random import randint

DEFAULT_COL = 0
DEFAULT_ROW = 2


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
    app: Prodict
    _pos: ServiceDashPosition
    _build_options: Prodict
    _env: Prodict
    app_ts: int
    methods: List[MethodRegistration]
    name: str
    pos_filled: bool
    title: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = Prodict()
        self._pos = ServiceDashPosition()
        self.methods = []
        self._env = Prodict()
        self._build_options = Prodict()

    @property
    def config(self):
        return dict(
            env=self._env, pos=self._pos, build_options=self._build_options)

    def state(self):
        data = (self.app or {}).copy()
        data.update(
            dict(
                methods=self.methods,
                name=self.name,
                title=self.title,
                pos=self.pos,
                sla=randint(98, 99),
                mem=randint(1, 3),
                cpu=randint(1, 3),
            ))
        return data

    @property
    def pos(self):
        return self._pos

    def set_title(self, title):
        if title:
            self.title = title

    def set_name(self, name):
        self.name = name

    def is_active(self):
        if self.app_ts:
            if time() > self._state[name].app_ts + self.timeout:
                return True
        return False

    def set_build_opts(self, **kwargs):
        if 'env' in kwargs:
            self._build_options.env = kwargs['env']
        if 'nocache' in kwargs:
            self._build_options.nocache = str2bool(kwargs['nocache'])
        if 'auto_remove' in kwargs:
            self._build_options.auto_remove = str2bool(kwargs['auto_remove'])

    def set_pos(self, col, row):
        if nn(col) and nn(row):
            self._pos.col = col
            self._pos.row = row

    def set_app(self, app):
        self.app = app
        self.app_ts = time()
        if 'register' in app:
            self.methods = []
            for method in app['register']:
                rec = method.copy()
                rec.update(service=self.name)
                self.methods.append(rec)


class State:
    def __init__(self):
        self.cols = 6
        self.rows = 6
        self.timeout = 30
        self._state = defaultdict(ServiceState)

    @property
    def state(self):
        return self._state

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __getitem__(self, name):
        srv = self._state[name]
        srv.set_name(name)
        return srv

    def __contains__(self, name):
        return name in self._state

    def values(self):
        return self._state.values()

    def __allocate(self, name, col=DEFAULT_COL, row=DEFAULT_ROW):
        """
        Allocating dashboard position for container close to wanted
        """
        print('allocating pos', name, col, row)
        occupied = []
        for srv in self._state.values():
            if srv.name != name and nn(srv.pos.col and nn(srv.pos.row)):
                occupied.append(srv.pos.to_s())

        print('occupied', occupied)
        for icol, irow in self.__space_walk(int(col), int(row)):
            key = f"{icol}x{irow}"
            if key not in occupied:
                return dict(col=icol, row=irow)

    def __space_walk(self, scol=0, srow=0):
        """
        Yields all possible positions
        """
        for rowi in [str(row) for row in range(int(srow), self.rows)]:
            for coli in [str(col) for col in range(int(scol), self.cols)]:
                yield coli, rowi

    def update(self, name, status=None, config=None, meta=None):
        # applying config if present
        srv = self[name]
        # allocating position for dashboard if not
        if not srv.pos:
            if config and nn(config) and nn(config.pos.row) and nn(
                    config.pos.col):
                pos = self.__allocate(
                    name, col=config.pos.col, row=config.pos.row)
            elif meta and nn(meta.col) and nn(meta.row):
                pos = self.__allocate(name, col=meta.col, row=meta.row)
            else:
                pos = self.__allocate(name)
            srv.set_pos(**pos)

        # making title
        if meta and meta.title:
            srv.set_title(meta.title)
        else:
            srv.set_title(name.title())

        # updating status if present
        if status:
            srv.set_app(status)

        return srv

    def get_appstatus(self, name):
        """
        Get status receved from application
        """
        return self[name].app
