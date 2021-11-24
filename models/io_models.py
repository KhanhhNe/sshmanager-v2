from datetime import datetime

from pydantic import BaseModel


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
    is_connected_to_ssh: bool
    last_checked: datetime = None

    class Config:
        orm_mode = True


class SettingsInOut(BaseModel):
    ssh_tasks_count: int
    port_tasks_count: int
    web_workers_count: int
    web_port: int


class SettingsUpdateResult(BaseModel):
    need_restart: bool


class PluginIn(BaseModel):
    code: str
    name: str


class PluginOut(BaseModel):
    code: str
    name: str
