from http import HTTPStatus
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from requests_oauthlib import OAuth2Session
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import get_session
from app.models import User
from app.service.jwtoken import JWToken
from app.settings import config

from .schemas import AuthLoginResponse
from .schemas import GoogleUser

AsyncSession = Annotated[async_sessionmaker, Depends(get_session)]

OAUTH_CONFIG = {
    "GOOGLE": {
        "TOKEN_URL": "https://accounts.google.com/o/oauth2/token",
        "USERINFO_URL": "https://www.googleapis.com/oauth2/v1/userinfo",
        "REDIRECT_URL": f"{config.base_url}/api/v1/auth/google/callback",
    },
    "GITHUB": {
        "TOKEN_URL": "https://github.com/login/oauth/access_token",
        "USERINFO_URL": "https://api.github.com/user",
        "REDIRECT_URL": f"{config.base_url}/api/v1/auth/github/callback",
    },
}

# class AuthLogin:

#     def __init__(
#         self,
#         session: AsyncSession,
#     ) -> None:
#         self.dbsession = session

#     async def execute(self, username: str, password: str) -> str:
#         ipbuser = await ipbauth.login(username, password)

#         async with self.dbsession() as session:
#             user = await User.get_by_id(session, ipbuser.mahasiswa_id)
#             if user is None:
#                 await User.create(session, ipbuser.mahasiswa_id,
#                                   ipbuser.username, ipbuser.nama, False)

#         return ipbuser.token


class AuthGoogleCallback:

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.dbsession = session
        self.oauth = OAuth2Session(
            client_id=config.oauth.client_id,
            redirect_uri="postmessage",
        )

    async def execute(self, code: str) -> AuthLoginResponse:
        _ = self.oauth.fetch_token(OAUTH_CONFIG["GOOGLE"]["TOKEN_URL"],
                                   code,
                                   client_secret=config.oauth.client_secret)

        res = self.oauth.get(OAUTH_CONFIG["GOOGLE"]["USERINFO_URL"])
        data: GoogleUser = res.json()

        async with self.dbsession() as session:
            user = await User.get_by_username(session, data["email"])
            if user is None:
                user = await User.create(session,
                                         username=data["email"],
                                         realname=data["name"],
                                         is_admin=False)

        token = JWToken.encode(user.username)

        return AuthLoginResponse(token_type="bearer", access_token=token)
