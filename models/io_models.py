from datetime import datetime

from pydantic import BaseModel, create_model

import config


class SSHIn(BaseModel):
    ip: str
    username: str
    password: str


class SSHOut(BaseModel):
    ip: str
    username: str
    password: str
    is_live: bool
    is_checking: bool
    last_checked: datetime = None

    class Config:
        orm_mode = True


class PortIn(BaseModel):
    port: int


class PortOut(BaseModel):
    port: int
    ssh: SSHOut = None
    ip: str = ''
    is_checking: bool
    time_connected: datetime = None
    last_checked: datetime = None

    class Config:
        orm_mode = True


SettingsInOut = create_model('SettingsInOut', **config.PYDANTIC_ARGS)


class SettingsUpdateResult(BaseModel):
    need_restart: bool


class PluginIn(BaseModel):
    code: str
    name: str


class PluginOut(BaseModel):
    code: str
    name: str
