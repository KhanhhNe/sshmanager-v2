from datetime import datetime

from pydantic import BaseModel, create_model, validator

import config


class SSHIn(BaseModel):
    ip: str
    username: str = None
    password: str = None


class SSHOut(BaseModel):
    id: int
    ip: str
    username: str
    password: str
    is_live: bool
    is_checking: bool
    last_checked: datetime = None
    status_text: str = None

    class Config:
        orm_mode = True

    # noinspection PyMethodParameters
    @validator('status_text', pre=True, always=True)
    def default_status_text(cls, v, values):
        if not v and values['last_checked']:
            return 'live' if values['is_live'] else 'die'
        elif values['is_live']:
            return 'live'
        else:
            return v or ''


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
