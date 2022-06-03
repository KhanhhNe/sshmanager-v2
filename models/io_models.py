import json
from typing import Dict, Type

from pony.orm.core import Attribute, EntityMeta
from pydantic import BaseConfig, BaseModel, Field, Json, create_model, validator

import config
from models import Port, SSH


def generate_pydantic_model(entity: Type[EntityMeta], model_name, field_description: Dict[str, str]):
    class Config(BaseConfig):
        orm_mode = True

    entity_name = repr(entity.__name__)
    result = {}
    relationship_fields = []

    description_missing = []
    attr: Attribute
    # noinspection PyProtectedMember,PyArgumentList
    for attr in entity._get_attrs_(exclude=['classtype']):
        if attr.is_relation:
            attr_type = Json
            relationship_fields.append(attr.name)
        else:
            attr_type = attr.py_type

        args = {}
        if not attr.is_required:
            args['default'] = None
        if attr.name in field_description:
            args['description'] = field_description[attr.name]
        else:
            description_missing.append(attr.name)

        result[attr.name] = (attr_type, Field(**args))

    if description_missing:
        missing_display = ', '.join(map(repr, description_missing))
        print(json.dumps({i: '' for i in description_missing}, indent=4))
        raise KeyError(f"No description found of entity {entity_name} for attributes: {missing_display}")

    redundant_fields = []
    for name in field_description:
        if name not in result:
            redundant_fields.append(name)
    if redundant_fields:
        redundant_display = ', '.join(map(repr, redundant_fields))
        raise KeyError(f"Redundant description found of entity {entity_name} for attributes: {redundant_display}")

    @validator(*relationship_fields, pre=True, always=True, allow_reuse=True)
    def relationship_validator(cls, v):
        if v:
            return json.dumps(v.to_dict(), default=str)

    return create_model(model_name,
                        __config__=Config,
                        __validators__={'relationship_validator': relationship_validator},
                        **result)


class SSHIn(BaseModel):
    ip: str
    username: str = None
    password: str = None


SSHOutBase = generate_pydantic_model(SSH, 'SSHOutBase', {
    "id": "",
    "is_checking": "SSH đang được kiểm tra fresh",
    "last_checked": "Thời điểm được kiểm tra gần nhất",
    "last_modified": "Thời điểm cập nhật gần nhất",
    "ip": "IP của SSH",
    "username": "Username của SSH",
    "password": "Mật khẩu đăng nhập SSH",
    "is_live": "SSH live và sử dụng được",
    "port": "ID của Port mà SSH này gán vào"
})


class SSHOut(SSHOutBase):
    status_text: str = None

    # noinspection PyMethodParameters
    @validator('status_text', pre=True, always=True, check_fields=False)
    def default_status_text(cls, v, values):
        if v:
            return v
        return {
            True: 'live',
            False: 'die'
        }.get(values['is_live'], '')


class PortIn(BaseModel):
    port_number: int


PortOut = generate_pydantic_model(Port, 'PortOut', {
    "id": "",
    "is_checking": "Port đang được kiểm tra kết nối",
    "last_checked": "Thời điểm Port được kiểm tra gần nhất",
    "last_modified": "Thời điểm Port được cập nhật gần nhất",
    "port_number": "Cổng trong máy local được quản lý bởi Port",
    "auto_connect": "Tự động kết nối SSH đến Port",
    "ssh": "ID của SSH được sử dụng cho Port",
    "is_connected": "Port đã được kết nối đến SSH",
    "public_ip": "IP bên ngoài của proxy từ Port",
    "time_connected": "Thời điểm Port kết nối đến SSH",
    "proxy_address": "Địa chỉ proxy của Port"
})

SettingsInOut = create_model('SettingsInOut', **config.PYDANTIC_ARGS)


class SettingsUpdateResult(BaseModel):
    need_restart: bool
