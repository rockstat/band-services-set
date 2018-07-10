from prodict import Prodict
from pprint import pprint
from typing import List
from .constants import STATUS_RUNNING


class BCP(Prodict):
    PublicPort: int


class BC(Prodict):
    Ports: List[BCP]


class BandContainerBuilder():
    def __init__(self, image):
        self.image = image

    def run_struct(self, name, network, memory, bind_ip, host_ports,
                   auto_remove, etc_hosts, env, **kwargs):
        return Prodict.from_dict({
            'Image': self.image.id,
            'Hostname': name,
            'Cmd': self.image.cmd,
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
                    for hp, p in zip(host_ports, self.image.ports)
                },
                'ExtraHosts':
                [f"{host}:{ip}" for host, ip in etc_hosts.items()],
                'NetworkMode': network,
                'Memory': memory
            }
        })


class BandContainer():
    def __init__(self, container):
        self.c = container
        self.d: BC = BC()
        self.copy()

    def copy(self):
        self.d: BC = BC.from_dict(self.c._container)

    def print(self):
        pprint(self.d)

    async def fill(self):
        await self.c.show()
        self.copy()
        return self

    async def ensure_filled(self):
        if not self.d.State:
            await self.c.show()
        self.copy()

    @property
    def name(self):
        if self.d.Names:
            return self.d.Names[0].strip('/')
        return self.d.Name.strip('/')

    @property
    def short_id(self):
        return self.d.Id[:12]

    @property
    def state(self):
        if isinstance(self.d.State, dict):
            return self.d.State.Status
        return self.d.State

    @property
    def running(self):
        return self.state == STATUS_RUNNING

    @property
    def ports(self):
        if self.d.Ports:
            return list(p.PublicPort for p in self.d.Ports)
        if self.d.HostConfig.PortBindings:
            return list(self.d.HostConfig.PortBindings.keys())
        return []

    @property
    def data(self):
        return self.d

    def labels(self):
        if self.d.Labels:
            return self.d.Labels
        elif self.d.Config and self.d.Config.Labels:
            return self.d.Config.Labels
        return {}

    def inband(self):
        lbs = self.labels()
        return lbs and bool(lbs.inband)

    @property
    def short_info(self):
        return Prodict(
            name=self.name, short_id=self.short_id, state=self.state)

    def __getattr__(self, name):
        if hasattr(self.c, name):
            return getattr(self.c, name)
