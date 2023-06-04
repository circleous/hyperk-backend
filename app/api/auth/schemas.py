from typing import Literal, TypedDict

from pydantic import BaseModel
from pydantic import EmailStr

from app.models import UserSchema


class IPBUser(BaseModel):
    mahasiswa_id: int
    nama: str
    username: str
    token: str


class GoogleUser(TypedDict):
    email: str
    name: str
    given_name: str


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthLoginResponse(BaseModel):
    token_type: Literal["bearer"]
    access_token: str


class AuthGetUserResponse(UserSchema):
    pass