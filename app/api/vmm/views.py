from http import HTTPStatus

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from starlette.authentication import requires

router = APIRouter(prefix="/vmm", tags=["vmm"])

# @router.get("/availableOS")
# @requires(["authenticated"])
