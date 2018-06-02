from band import settings, dome, logger
from prodict import Prodict
from time import time
from .docker_manager import DockerManager


class State(Prodict):
    state: Prodict = Prodict()

    def set_status(self, name, app):
        self.state[name] = Prodict(app=app, app_ts=time())

    def clear_status(self, name):
        self.state[name].clear()

    def get_appstatus(self, name):
        state = self.state[name]
        if state and state.app:
            if time() - state.app_ts < 60:
                return state.app
        return {}


logger.info('Starting director api')
state = State()
dock = DockerManager(**settings)

from . import api
