from acutisapi.app import app
from acutisapi import logs


def run(flog=False):
    logs.init_log(flog)
    app.run()
