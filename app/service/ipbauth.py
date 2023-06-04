from http import HTTPStatus

from cache import AsyncTTL
from fastapi import HTTPException
import httpx
from pydantic import BaseModel

from app.models import User


class IPBUser(BaseModel):
    mahasiswa_id: int
    nama: str
    username: str
    token: str


async def login(username: str, password: str) -> IPBUser:
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.ipb.ac.id/v1/Authentication/LoginMahasiswa",
            headers={
                "X-IPB-API-Token": "Bearer 6454b1ff-7dce-396d-9b07-4f88248072b6"
            },
            json={
                "userName": username,
                "password": password,
            })
        if res.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED,
                                detail="INVALID_USERNAME_OR_PASSWORD")

        doc = res.json()
        return IPBUser(mahasiswa_id=doc.get("MahasiswaId"),
                       nama=doc.get("Nama"),
                       username=doc.get("Username"),
                       token=doc["Token"])


@AsyncTTL(time_to_live=3600, maxsize=1024)
async def verify_token(token: str) -> bool:
    async with httpx.AsyncClient() as client:
        # res = await client.get(
        #     "http://api.ipb.ac.id/v1/Authentication/ValidateToken",
        #     headers={
        #         "X-IPB-API-Token":
        #         "Bearer 6454b1ff-7dce-396d-9b07-4f88248072b6"
        #     },
        #     params={"token": token})
        # if res.status_code != HTTPStatus.OK:
        #     raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED,
        #                         detail="INVALID_TOKEN")
        # doc = res.json()
        # return doc.get("Valid", False)
        return True
