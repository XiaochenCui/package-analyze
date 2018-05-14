WEB_SOCKET_PORT = 4061

import getpass
username = getpass.getuser()
if username == 'root':
    RUN_AS_ROOT = True
else:
    RUN_AS_ROOT = False

try:
    from local_config import *
except ImportError:
    pass
