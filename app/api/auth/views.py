from http import HTTPStatus

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import Response
from starlette.authentication import requires

from app.settings import config

from .schemas import AuthGetUserResponse
from .schemas import AuthLoginResponse
from .use_cases import AuthGoogleCallback

router = APIRouter(prefix="/auth", tags=["auth"])

# @router.post("/login", response_model=AuthLoginResponse)
# async def login(
#         request: Request,
#         response: Response,
#         data: AuthLoginRequest,
#         use_case: AuthLogin = Depends(AuthLogin),
# ) -> AuthLoginResponse:
#     if not data.username or not data.password:
#         raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
#                             detail="Empty username or password.")

#     token = await use_case.execute(data.username, data.password)
#     response.set_cookie("access_token", token)

#     return AuthLoginResponse(access_token=token)


@router.get("/google/callback", response_model=AuthLoginResponse)
async def google_callback(
    request: Request,
    response: Response,
    code: str,
    use_case: AuthGoogleCallback = Depends(AuthGoogleCallback),
) -> AuthLoginResponse:
    if config.oauth.provider != "google":
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    res = await use_case.execute(code)
    response.set_cookie(
        "access_token",
        res.access_token,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return res


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str,
    use_case: AuthGoogleCallback = Depends(AuthGoogleCallback),
) -> AuthLoginResponse:
    if config.oauth.provider != "github":
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    return await use_case.execute(code)


@router.get("", response_model=AuthGetUserResponse)
@requires(["authenticated"])
async def get_user(request: Request) -> AuthGetUserResponse:
    return request.user