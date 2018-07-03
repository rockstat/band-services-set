from prodict import Prodict
from time import time
from band import logger

class State:
    def __init__(self):
        self.x = 6
        self.y = 6
        self.timeout = 30
        self.registry = Prodict()
        self.state = dict()
        self.init_matrix()

    def init_matrix(self):
        for x in range(0, self.x):
            self.registry[x] = dict()
            for y in range(0, self.y):
                self.registry[x][y] = None

    def get(self, x, y):
        return self.registry[x, y]

    def allocate(self):
        # offset =
        pass

    def gen(self):
        for x in range(0, self.x):
            for y in range(0, self.y):
                yield (self.registry[x][y], x, y)

    def set_status(self, name, app):
        self.state[name] = dict(app=app, app_ts=time())

    def clear_status(self, name):
        container_state = self.state.get(name, None)
        if container_state:
            container_state.clear()

    def check_expire(self):
        for k in self.state:
            container_state = self.state.get(k, None)
            if container_state and 'app_ts' in container_state:
                if time() - container_state['app_ts'] > self.timeout:
                    self.clear_status(k)


    def get_appstatus(self, name):
        container_state = self.state.get(name, None)
        if container_state and 'app' in container_state:
            if time() - container_state['app_ts'] < self.timeout:
                return container_state['app']
            else:
                logger.info("container state expired")
        return {}
