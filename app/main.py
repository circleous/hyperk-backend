from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth.views import router as auth_router
from app.api.instance.views import router as instance_router
import app.db as db
from app.middleware.auth import AuthenticationBackend
from app.middleware.auth import AuthenticationMiddleware
from app.service.virt import Virt
from app.service.virt import VirtMode
from app.settings import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.virtmanager = Virt(config.libvirt, VirtMode.READ | VirtMode.WRITE)

    yield

    db.virtmanager.conn.close()


app = FastAPI(title="hyperk",
              docs_url="/docs",
              redoc_url=None,
              lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=config.session_secret,
    max_age=1800,
    same_site="strict",
    https_only=config.env != "development",
)

app.add_middleware(AuthenticationMiddleware, backend=AuthenticationBackend())

apiv1 = APIRouter(prefix="/api/v1", tags=["apiv1"])
apiv1.include_router(auth_router)
apiv1.include_router(instance_router)

app.include_router(apiv1)

# @app.exception_handler(Exception)
# async def err_handler(request: Request, err: Exception) -> JSONResponse:
#     err_message = f"Failed to execute: {request.method} {request.url}"
#     return JSONResponse(
#         status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#         content={"message": f"{err_message}. Detail: {err.args}"})


@app.get("/", include_in_schema=False)
def index() -> JSONResponse:
    return JSONResponse({"status": "ok"})
