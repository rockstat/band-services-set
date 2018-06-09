import subprocess
from prodict import Prodict

from .constants import DEF_LABELS
from .helpers import tar_image_cmd



class BandImageBuilder:
    def __init__(self, img, img_options):
        self.img = img
        self.img_options = img_options

    async def __aenter__(self):
        self.p = subprocess.Popen(
            tar_image_cmd(self.img.path), stdout=subprocess.PIPE)
        return self

    def struct(self):
        return Prodict.from_dict({
            'fileobj': self.p.stdout,
            'encoding': 'identity',
            'tag': self.img.name,
            'nocache': self.img_options.get('nocache', False),
            'pull': self.img_options.get('pull', False),
            'labels': DEF_LABELS,
            'stream': True
        })

    async def __aexit__(self, exception_type, exception_value, traceback):
        self.p.kill()

class BandImage(Prodict):
    name: str
    path: str
    key: str
    base: str
    p: subprocess.Popen
    d: Prodict

    def set_data(self, data):
        self.d = Prodict.from_dict(data)
        return self

    @property
    def cmd(self):
        return self.d.Config.Cmd

    @property
    def id(self):
        return self.d.Id

    @property
    def ports(self):
        return list(self.d.ContainerConfig.ExposedPorts.keys())

    def create(self, img_options):
        return BandImageBuilder(self, img_options)

    def run_struct(self, name, network, memory, bind_ip, host_ports, auto_remove, env, **kwargs):
        return Prodict.from_dict({
            'Image': self.id,
            'Hostname': name,
            'Cmd': self.cmd,
            'Labels': {
                'inband': 'user'
            },
            'Env': [f"{k}={v}" for k, v in env.items()],
            'StopSignal': 'SIGTERM',
            'HostConfig': {
                'AutoRemove': auto_remove,
                # 'RestartPolicy': {'Name': 'unless-stopped'},
                'PortBindings': {
                    p: [{
                        'HostIp': bind_ip,
                        'HostPort': str(hp)
                    }]
                    for hp, p in zip(host_ports, self.ports)
                },
                'NetworkMode': network,
                'Memory': memory
            }
        })

