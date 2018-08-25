STATUS_RUNNING = 'running'
STATUS_STARTING = 'starting'
STATUS_RESTARTING = 'restarting'
STATUS_REMOVING = 'removing'
STATUS_STOPPING = 'stopping'
SYSTEM_CONTAINERS = [
    'chproxy', 'grafana', 'anaconda', 'openvpn', 'theia', 'heavyload',
    'frontier'
]
DEF_LABELS = {'inband': 'inband'}
STARTED_SET = 'started'
SERVICE_TIMEOUT = 30
DEFAULT_COL = 0
DEFAULT_ROW = 2

SHARED_CONFIG_KEY = '__shared__'