import os
import pathlib
import configparser
import platformdirs
from collections.abc import MutableMapping

SECTION_DEFAULT = 'default'
SECTION_AUTH = 'authentication'

_cp = configparser.ConfigParser()
_app_config_dir = platformdirs.AppDirs(appname="iotccli", version="alpha").user_config_dir
_app_config_file = os.path.join(_app_config_dir, "config.ini")
_is_initialized = False


def init() -> None:
    global _is_initialized
    if _is_initialized:
        return
    _is_initialized = True  # we should not attempt to init after the attempt below:
    if not os.path.isdir(_app_config_dir):
        try:
            pathlib.Path(_app_config_dir).mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError:
            print("Could not create app config directory %s" % _app_config_dir)
            return
    try:
        pathlib.Path(_app_config_file).touch()
        os.chmod(_app_config_file, 0o700)
    except OSError:
        print("Could not write to %s" % _app_config_file)
        return
    # triple check?
    if not os.access(_app_config_file, os.W_OK):
        print("File %s is not Writeable" % _app_config_file)
        return
    _cp.read(_app_config_file)


def is_valid() -> bool:
    return _cp.has_section(SECTION_AUTH)


def write() -> bool:
    try:
        with open(_app_config_file, 'w') as app_config_file:
            # PyCharm seems to get this wrong: Expected type 'SupportsWrite[str]', got 'TextIO' instead
            # noinspection PyTypeChecker
            _cp.write(app_config_file)
        return True
    except OSError:
        print("Could not write to %s" % _app_config_file)


# user can call this to lazy init section in preparation for read or write of individual section values
def get_section(section: str) -> MutableMapping:
    if not _cp.has_section(section):
        _cp[section] = {}
    return _cp[section]

# automatically init on load
init()
