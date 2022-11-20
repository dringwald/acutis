import sys
import logging
import http.client as http_client
import contextlib
from acutisapi.logpushoverhandler import LogPushoverHandler

LOG_FILE = "api.log"
LOG_STREAM = sys.stdout
PUSHOVER_KEYS = {"app_token":"a1c7f5g5pw2d7nxt1qb9bwcyesmped",
    "user_token":"u27psikhwywa2kba8a594zotexyvqs"}


logging.basicConfig(
    format="%(asctime)s > %(name)s/%(levelname)s : %(message)s",
    datefmt="%Y.%m.%d %k:%M",
    level=logging.DEBUG,
)

def enable_stream_log():
    stream_h = logging.StreamHandler(LOG_STREAM).setLevel(logging.DEBUG)
    logging.getLogger().addHandler(stream_h)

def enable_file_log():
    file_h = logging.FileHandler(LOG_FILE).setLevel(logging.INFO)
    logging.getLogger().addHandler(file_h)

def enable_push_log():
    pushlog : logging.Logger = logging.getLogger("push").setLevel(logging.DEBUG)
    push_handler = LogPushoverHandler(
        token=PUSHOVER_KEYS["app_token"],
        user=PUSHOVER_KEYS["user_token"]
    )
    push_handler.setFormatter(logging.Formatter('%(message)s'))
    pushlog.addHandler(push_handler)
    
def get_pushlog():
    return logging.getLogger("push") 


def debug_requests_on():
    """Switches on logging of the requests module."""
    http_client.HTTPConnection.debuglevel = 1

    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def debug_requests_off():
    """Switches off logging of the requests module, might be some side-effects"""
    http_client.HTTPConnection.debuglevel = 0

    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.WARNING)
    requests_log.propagate = False


@contextlib.contextmanager
def debug_requests():
    """Use with 'with'!

    with api_log.debug_request():
        requests.get(...)
    """
    debug_requests_on()
    yield
    debug_requests_off()
