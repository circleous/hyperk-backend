from typing import Annotated, Optional, TypedDict

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security.utils import get_authorization_scheme_param
import jwt
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.users import User
from app.settings import Config
from app.settings import get_config

whitelist = [
    "/api/v1/auth/google/callback",
    "/api/v1/auth/github/callback",
]

UnauthorizedError = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


class JWTPayload(TypedDict):
    iss: str
    sub: str
    iat: int
    exp: int
    nbf: int
    jti: str


async def get_current_user(
    request: Request,
    config: Annotated[Config, Depends(get_config)],
    dbsession: Annotated[async_sessionmaker[AsyncSession],
                         Depends(get_session)],
) -> None:
    if request.url.path in whitelist:
        return None

    authorization = request.headers.get("authorization")
    if not authorization:
        token = request.cookies.get("access_token")
    else:
        _, token = get_authorization_scheme_param(authorization)

    if not token:
        raise UnauthorizedError

    try:
        payload: JWTPayload = jwt.decode(
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
                "require": ["jti",],
            },
        )
    except jwt.PyJWTError:
        raise UnauthorizedError

    principal = payload["sub"]

    async with dbsession() as session:
        user = await User.get_by_username(session, principal)
        if user is None:
            raise UnauthorizedError
        request.scope["user"] = user

    return None
