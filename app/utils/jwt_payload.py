from pydantic import BaseModel


class JwtPayload(BaseModel):
    id: int
    nickname: str
