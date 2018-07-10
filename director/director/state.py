from prodict import Prodict
from time import time
from band import logger
import ujson


class State:
    def __init__(self):
        self.maxx = 6
        self.maxy = 6
        self.timeout = 30
        self.positions = Prodict.from_dict(
            {x: {y: None
                 for y in self.yrange()}
             for x in self.xrange()})
        self._state = dict()
        self.last_key = 0

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __getitem__(self, name):
        return self._state.get(name, None)

    @property
    def state(self):
        return self._state

    def xrange(self, start=0):
        return [str(x) for x in range(int(start), self.maxx)]

    def yrange(self, start=0):
        return [str(y) for y in range(int(start), self.maxy)]

    def allocate(self, name, x=0, y=2):
        x = str(x)
        y = str(y)
        for x, y in self.iterate(x, y):
            if self.positions[x][y] == None:
                self.positions[x][y] = name
                return (x, y)

    def iterate(self, x=0, y=0):
        for yi in self.xrange(y):
            for xi in self.yrange(x):
                yield (
                    xi,
                    yi,
                )

    def set_state(self, name, status=None, config=None, meta=None):
        # ensure container state is created
        container_state = self._state.get(name, None)
        if not container_state:
            container_state = self._state[name] = Prodict(config={}, app={})
        # allocating position for dashboars
        if not container_state.config.pos:
            if config and config.get('pos'):
                x, y = config.get('pos')
                pos = self.allocate(name, x, y)
            elif meta and meta.get('xpos', None) and meta.get('ypos', None):
                pos = self.allocate(name, meta.get('xpos'), meta.get('ypos'))
            else:
                pos = self.allocate(name)
            container_state.config.pos = pos
        # making title
        if not container_state.title:
            container_state.title = meta and meta.get('title', None) or name.title()
        # updating status if present
        if status:
            container_state.app = status
            container_state.app_ts = time()
        return container_state

    def registraions(self):
        """
        Get actual registrations
        """
        return dict({k: self.get_appstatus(k) for k in self._state.keys()})

    def clear_status(self, name):
        container_state = self._state.get(name, None)
        if container_state:
            container_state.clear()

    def get_appstatus(self, name):
        """
        Get status receved from application
        """
        container_state = self._state.get(name, None)
        if container_state and 'app' in container_state:
            # check actual/expired
            if time() - container_state['app_ts'] < self.timeout:
                return container_state['app']
            else:
                self.clear_status(name)
        return {}
