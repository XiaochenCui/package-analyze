# Interval between terminal upload real-time status
REPORT_STATUS_INTERVAL = 10

WEB_SOCKET_PORT = 4021

try:
    from local_config import *
except ImportError:
    pass
