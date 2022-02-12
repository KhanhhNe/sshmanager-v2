from datetime import datetime

from pydantic import BaseModel, create_model

import config


class SSHIn(BaseModel):
    ip: str
    username: str
    password: str


class SSHOut(BaseModel):
    id: int
    ip: str
    username: str
    password: str
    is_live: bool
    is_checking: bool
    last_checked: datetime = None

    class Config:
        orm_mode = True


class PortIn(BaseModel):
    port_number: int


class PortOut(BaseModel):
    id = int
    port_number: int
    ssh: SSHOut = None
    external_ip: str = None
    time_connected: datetime = None
    is_checking: bool
    last_checked: datetime = None

    class Config:
        orm_mode = True


SettingsInOut = create_model('SettingsInOut', **config.PYDANTIC_ARGS)


class SettingsUpdateResult(BaseModel):
    need_restart: bool
