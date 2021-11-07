from fastapi.routing import APIRouter

import config
from models.io_models import SettingsInOut, SettingsUpdateResult

router = APIRouter()


@router.get('/')
def get_all_settings():
    """
    Get all settings
    """
    conf = config.get_config()
    return SettingsInOut(
        ssh_tasks_count=conf.getint('SSH', 'tasks_count'),
        port_tasks_count=conf.getint('PORT', 'tasks_count'),
        web_workers_count=conf.getint('WEB', 'workers'),
        web_port=conf.getint('WEB', 'port'),
    )


@router.post('/')
def update_settings(settings: SettingsInOut):
    """
    Update settings
    """
    conf = config.get_config()
    if conf.getint('WEB', 'workers') != settings.web_workers_count or \
            conf.getint('WEB', 'port') != settings.web_port:
        need_restart = True
    else:
        need_restart = False

    conf['SSH']['tasks_count'] = str(settings.ssh_tasks_count)
    conf['PORT']['tasks_count'] = str(settings.port_tasks_count)
    conf['WEB']['workers'] = str(settings.web_workers_count)
    conf['WEB']['port'] = str(settings.web_port)
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
    return {
        'ssh_tasks_count': "Số thread check SSH live/die",
        'port_tasks_count': "Số thread check trạng thái Port",
        'web_workers_count': "Số workers chạy web",
        'web_port': "Port chạy web"
    }
