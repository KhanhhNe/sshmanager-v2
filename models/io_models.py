from pydantic import BaseModel


class SSHInfo(BaseModel):
    ip: str
    username: str
    password: str
