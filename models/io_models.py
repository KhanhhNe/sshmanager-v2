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
    last_checked: datetime

    class Config:
        orm_mode = True


class PortIn(BaseModel):
    port: int


class PortOut(BaseModel):
    port: int
    ssh: SSHOut
    ip: str
    is_checking: bool
    is_connected_to_ssh: bool
    last_checked: datetime

    class Config:
        orm_mode = True
