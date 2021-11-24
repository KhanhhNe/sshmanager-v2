import os
from os.path import join

from fastapi.routing import APIRouter

from models.io_models import PluginIn, PluginOut

router = APIRouter()


@router.get('/')
def get_all_plugins():
    """
    Get all plugins.
    """
    return [PluginOut(
        name=filename,
        code=open(join('plugins', filename), encoding='utf-8').read()
    ) for filename in os.listdir('plugins')]


@router.post('/')
def create_new_plugin(plugin: PluginIn):
    filepath = join('plugins', plugin.name)
    open(filepath, 'w+', encoding='utf-8').write(plugin.code)
    return {'success': True}


@router.delete('/')
def remove_plugin(plugin_name: str):
    plugin_path = join('plugins', plugin_name)
    if os.path.exists(plugin_path):
        os.remove(plugin_path)
        return {'success': True}
    else:
        return {'success': False}
