import logging as _logging

from . import abreviations
from . import mps_data
from . import pathmatcher
from . import scripts
from . import utils
from .mps_data import MPSData
from .pathmatcher import PathMatcher

_logging.basicConfig(level=_logging.INFO)
_loggers = [getattr(m, "logger") for m in [pathmatcher, scripts]]


def set_log_level(level=_logging.INFO):

    for logger in _loggers:
        logger.setLevel(level)


set_log_level()

__all__ = [
    "utils",
    "mps_data",
    "MPSData",
    "pathmatcher",
    "PathMatcher",
    "abreviations",
    "scripts",
    "set_log_level",
]
