import logging
import time
from contextlib import contextmanager


@contextmanager
def time_func(msg: str):
    logging.info("Beginning to run %s", msg)
    time_before_call = time.monotonic()
    yield
    logging.info("%s took %s seconds", msg, round(time.monotonic() - time_before_call, 3))
