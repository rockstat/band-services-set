from prodict import Prodict
from time import time

class State(Prodict):
    state: Prodict = Prodict()

    def set_status(self, name, app):
        self.state[name] = Prodict(app=app, app_ts=time())

    def clear_status(self, name):
        state = self.state.get(name, None)
        if state:
            state.clear()

    def get_appstatus(self, name):
        state = self.state.get(name, None)
        if state and state.app:
            if time() - state.app_ts < 60:
                return state.app
        return {}

