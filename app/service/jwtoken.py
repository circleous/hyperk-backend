from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Dict, Optional, TypedDict
from uuid import uuid4

import jwt

from app.settings import config


class JWTPayload(TypedDict):
    iss: str
    sub: str
    iat: int
    exp: int
    nbf: int
    jti: str


class JWToken:

    @staticmethod
    def encode(principal: str, expiry: timedelta = timedelta(days=30)) -> str:
        now = datetime.now(timezone.utc)
        payload: JWTPayload = {
            "iss": config.base_url,
            "sub": principal,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + expiry).timestamp()),
            "jti": str(uuid4()),
        }
        token = jwt.encode(
            payload=payload,  # type: ignore
            key=config.jwt_secret,
            algorithm="HS512",
        )
        return token

    @staticmethod
    def decode(token: str) -> JWTPayload:
        return jwt.decode(  # type: ignore
            token,
            key=config.jwt_secret,
            issuer=config.base_url,
            algorithms=["HS512"],
            verify=True,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_iss": True,
                "require": [
                    "jti",
                ],
            },
        )
