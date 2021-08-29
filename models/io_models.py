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
    last_checked: datetime

    class Config:
        orm_mode = True
