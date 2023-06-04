from pydantic import BaseModel

from app.models import UserSchema


class IPBUser(BaseModel):
    mahasiswa_id: int
    nama: str
    username: str
    token: str


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthLoginResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str


class AuthGetUserResponse(UserSchema):
    pass