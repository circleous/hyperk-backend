from http import HTTPStatus
import logging
from typing import List, Optional

from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.security.utils import get_authorization_scheme_param
import jwt
from starlette.authentication import AuthCredentials
from starlette.authentication import \
    AuthenticationBackend as BaseAuthenticationBackend
from starlette.authentication import AuthenticationError
from starlette.middleware.authentication import \
    AuthenticationMiddleware as BaseAuthenticationMiddleware
from starlette.requests import HTTPConnection

from app.db import get_session
from app.models import User
from app.models import UserSchema
from app.service.jwtoken import JWToken

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseAuthenticationMiddleware):

    @staticmethod
    def default_on_error(conn: HTTPConnection, exc: Exception) -> JSONResponse:
        logger.error("auth error: %s", exc.args)
        """
        Overriden method just to make sure we return response in our format.
        :param conn: HTTPConnection of the current request-response cycle
        :param exc: Any exception that could have been raised
        :return: JSONResponse with error data as dict and 403 status code
        """
        return JSONResponse(status_code=HTTPStatus.FORBIDDEN,
                            content={"error": "FORBIDDEN"})


class AuthenticationBackend(BaseAuthenticationBackend):

    async def authenticate(  # type: ignore
        self,
        request: HTTPConnection,
    ) -> tuple[AuthCredentials, Optional[UserSchema]]:
        authorization = request.headers.get("Authorization")
        if authorization is None:
            # try getting value from cookie
            token = request.cookies.get("access_token")
            if not token:
                return AuthCredentials(), None
        else:
            scheme, token = get_authorization_scheme_param(authorization)
            if not (scheme and token):
                return AuthCredentials(None), None
            if scheme.lower() != "bearer":
                return AuthCredentials(None), None

        # valid = await verify_token(token)
        # if not valid:
        #     return AuthCredentials(None), None

        try:
            data = JWToken.decode(token)
        except jwt.exceptions.PyJWTError as exc:
            return AuthCredentials(None), None

        Session = await anext(get_session())
        async with Session() as session:
            user = await User.get_by_username(session, data["sub"])
            if user is None:
                return AuthCredentials(None), None

            scopes = ["authenticated"]
            if user.is_admin:
                scopes.append("admin")

        return AuthCredentials(scopes), UserSchema.from_orm(user)
