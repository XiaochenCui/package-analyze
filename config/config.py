WEB_SOCKET_PORT = 4061

REDIS_HOST = 'redis'
REDIS_PORT = 6380

import getpass
username = getpass.getuser()
if username == 'root':
    RUN_AS_ROOT = True
    REDIS_PORT = 6379
else:
    RUN_AS_ROOT = False

try:
    from local_config import *
except ImportError:
    pass
