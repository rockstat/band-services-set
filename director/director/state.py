from prodict import Prodict
from time import time

class State(Prodict):
    state: Prodict = Prodict()
    timeout: int = 15

    def set_status(self, name, app):
        self.state[name] = Prodict(app=app, app_ts=time())

    def clear_status(self, name):
        status = self.state.get(name, None)
        if status:
            status.clear()

    def check_expire(self):
        for k in self.state:
            if self.state[k] and self.state[k].app_ts:
                if time() - self.state[k].app_ts > self.timeout:
                    self.clear_status(k)

    
    def get_appstatus(self, name):
        status = self.state.get(name, None)
        if status and status.app:
            if time() - status.app_ts < self.timeout:
                return status.app
        return {}

