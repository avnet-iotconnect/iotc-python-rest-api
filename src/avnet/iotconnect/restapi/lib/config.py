import configparser
import os
import pathlib
from collections.abc import MutableMapping

import platformdirs

SECTION_AUTH = 'authentication'

_cp = configparser.ConfigParser()
_app_cache_dir = platformdirs.AppDirs(appname="iotccli", version="alpha").user_cache_dir
_app_config = _app_cache_dir + "/config.ini"


def init(quiet = True) -> bool:
    if not is_loaded():
        load(quiet)
    return is_loaded()


def is_loaded() -> bool:
    return _cp.has_section(SECTION_AUTH)


def load(quiet = True) -> bool:
    if not os.path.isdir(_app_cache_dir):
        try:
            pathlib.Path().mkdir(mode=755, parents=True, exist_ok=True)
        except OSError:
            if not quiet:
                print("Could not create app cache directory %s" % _app_cache_dir)
            return False
    if not os.access(_app_config, os.W_OK):
        if not quiet:
            print("File %s is not Writeable" % _app_config)
        return False
    _cp.read(_app_config)
    return is_loaded()

def write(quiet = True) -> bool:
    try:
        with open(_app_config, 'w') as app_config_file:
            # PyCharm seems to get this wrong: Expected type 'SupportsWrite[str]', got 'TextIO' instead
            # noinspection PyTypeChecker
            _cp.write(app_config_file)
        return True
    except OSError:
        if not quiet:
            print("Could not write to %s" % _app_config)
        return False


def get_section(section: str) -> MutableMapping:
    init()
    if not _cp.has_section(section):
        _cp[section] = {}
    return _cp[section]
