import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)
router = APIRouter()

Status = Literal["ok", "error"]


class ReadinessResponse(BaseModel):
    status: Status
    checks: dict[str, Status]


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(session: AsyncSession = Depends(get_session)) -> ReadinessResponse:
    try:
        await session.execute(text("SELECT 1"))
        database_status: Status = "ok"
    except SQLAlchemyError:
        logger.exception("Database readiness check failed")
        database_status = "error"

    vector_status: Status = (
        "ok" if vector_store.heartbeat() else "error"
    )
    checks: dict[str, Status] = {
        "database": database_status,
        "vector_store": vector_status,
    }
    status: Status = "ok" if all(value == "ok" for value in checks.values()) else "error"
    response = ReadinessResponse(status=status, checks=checks)

    if status == "error":
        raise HTTPException(status_code=503, detail=response.model_dump())

    return response
