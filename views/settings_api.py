from fastapi.routing import APIRouter

import config
from models.io_models import SettingsInOut, SettingsUpdateResult

router = APIRouter()


@router.get('/')
def get_all_settings():
    """
    Get all settings
    """
    args = {
        i.full_name: config.get_config_value(i) for i in config.DEFAULT_CONFIG
    }
    return SettingsInOut(**args)


@router.post('/')
def update_settings(settings: SettingsInOut):
    """
    Update settings
    """
    conf = config.get_config()
    need_restart = False

    for item in config.DEFAULT_CONFIG:
        old = config.get_config_value(item)
        new = getattr(settings, item.full_name)
        if new != old and item.need_restart:
            need_restart = True

        conf[item.section][item.name] = str(new)

    config.write_config(conf)

    return SettingsUpdateResult(need_restart=need_restart)


@router.delete('/')
def reset_all_settings():
    """
    Resset all settings to default values
    """
    config.reset_config()


@router.get('/names/')
def get_settings_names():
    """
    Get settings display names
    """
    names = {}
    for item in config.DEFAULT_CONFIG:
        names[item.full_name] = item.description
    return names
