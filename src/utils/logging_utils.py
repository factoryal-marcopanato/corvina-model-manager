import logging
import os
import sys


def setup_logging() -> logging.Logger:
    if 'l0' in globals():
        return globals()['l0']

    handlers = [logging.StreamHandler(stream=sys.stdout)]
    logging.basicConfig(
        format="%(asctime)s [%(levelname)-5s] [%(name)s.%(funcName)s] %(message)s",
        level=logging.ERROR,
        handlers=handlers,
    )
    # logging.getLogger('root').setLevel(logging.DEBUG)  # Enable DEBUG log everywhere
    l0 = logging.getLogger("app")
    l0.setLevel(logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO")))
    globals()['l0'] = l0

    return l0
