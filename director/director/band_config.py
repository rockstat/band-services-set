import ujson
import yaml
import time
import os


class BandConfig:
    def __init__(self):
        self.dir_path = './data'
        self.latest = 'latest.yml'

    def config_dir(self, name):
        return f"{self.dir_path}/container_{name}"

    def prepare_dir(self, name):
        path = self.config_dir(name)
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def new_name(self):
        return f"{time.strftime('%Y%m%d%H%M%S')}.yml"
        

    def encode(self, **data):
        return yaml.dump(data, default_flow_style=False)

    def save_config(self, name, params):
        path = self.prepare_dir(name)
        current = self.load_config(name)
        if current:
            current.pop('created_at', None)
            if current == params:
                return
        raw = self.encode(**params, created_at=time.asctime())
        for file in [self.latest, self.new_name()]:
            with open(f"{path}/{file}", 'w') as f:
                f.write(raw)

    def load_config(self, name):
        conf = f"{self.config_dir(name)}/{self.latest}"
        if os.path.isfile(conf):
            with open(conf, 'r') as f:
                content = f.read()
                return yaml.load(content)