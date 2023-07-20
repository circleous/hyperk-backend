from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.auth.views import router as auth_router
from app.api.instance.views import router as instance_router
from app.security.auth import get_current_user
from app.settings import get_config

config = get_config()

app = FastAPI(
    title="hyperk",
    docs_url="/docs",
    redoc_url=None,
    dependencies=[
        Depends(get_current_user),
    ],
)

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
