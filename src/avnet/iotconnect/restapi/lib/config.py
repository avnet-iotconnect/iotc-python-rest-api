import configparser
import os
import pathlib
from collections.abc import MutableMapping

import platformdirs

CONFIG_VERSION = "1.0" # for future compatibility and potential conversion

SECTION_DEFAULT = 'default'
SECTION_SETTINGS = 'settings'
SECTION_AUTH = 'authentication'

_cp = configparser.ConfigParser()
_app_config_dir = platformdirs.AppDirs(appname="iotc").user_config_dir
_app_config_file = os.path.join(_app_config_dir, "config.ini")
_is_initialized = False

api_trace_enabled = True if os.environ.get("IOTC_API_TRACE") is not None else False


def init() -> None:
    global _is_initialized, api_trace_enabled
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

    # override only if environment variable is not set
    if not api_trace_enabled:
        api_trace_enabled = _cp.has_section(SECTION_SETTINGS) and _cp.getboolean(SECTION_SETTINGS, "api-trace")


def is_valid() -> bool:
    return _cp.has_section(SECTION_AUTH)


def write() -> bool:
    try:
        with open(_app_config_file, 'w') as app_config_file:
            _cp.add_section(SECTION_DEFAULT)
            default = get_section(SECTION_DEFAULT)
            default.version = CONFIG_VERSION
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
