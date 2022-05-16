import json
from typing import Dict

from fastapi.routing import APIRouter

import config
from models.io_models import SettingsInOut, SettingsUpdateResult

router = APIRouter()


@router.get('', response_model=SettingsInOut)
def get_all_settings():
    """
    Lấy thông tin mọi Settings.

    :return: Danh sách thông tin Settings
    """
    args = {
        i.full_name: config.get_by_item(i) for i in config.DEFAULT_CONFIG
    }
    return SettingsInOut(**args)


@router.post('', response_model=SettingsUpdateResult)
def update_settings(settings: SettingsInOut):
    """
    Cập nhật Settings.

    :param settings: Thông tin Settings mới

    :return:
    """
    conf = config.get_config()
    need_restart = False

    for item in config.DEFAULT_CONFIG:
        old = config.get_by_item(item)
        new = getattr(settings, item.full_name)
        if new != old and item.need_restart:
            need_restart = True

        conf[item.section][item.name] = json.dumps(new)

    config.write_config(conf)

    return SettingsUpdateResult(need_restart=need_restart)


@router.delete('')
def reset_all_settings():
    """
    Đặt lại toàn bộ Settings.

    :return:
    """
    config.reset_config()


@router.get('/names', response_model=Dict[str, str])
def get_settings_names():
    """
    Lấy thông tin tên hiển thị của các Settings.

    :return: Tên hiển thị của các Settings
    """
    names = {}
    for item in config.DEFAULT_CONFIG:
        names[item.full_name] = item.description
    return names
