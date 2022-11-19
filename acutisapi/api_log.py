import sys
import logging
import http.client as http_client
import contextlib


LOG_FILE = "api.log"
LOG_STREAM = sys.stdout


def init_log():

    logging.basicConfig(
        format="%(asctime)s > %(name)s/%(levelname)s : %(message)s",
        datefmt="%Y.%m.%d %k:%M",
        level=logging.DEBUG,
    )

    if LOG_FILE:
        file_h = logging.FileHandler(LOG_FILE).setLevel(logging.INFO)
        logging.getLogger().addHandler(file_h)

    if LOG_STREAM:
        stream_h = logging.StreamHandler(LOG_STREAM).setLevel(logging.DEBUG)
        logging.getLogger().addHandler(stream_h)


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
