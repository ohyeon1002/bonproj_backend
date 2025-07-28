from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..models import User
from ..schemas import ResultSetWithResult
from ..database import get_db
from ..dependencies import get_current_active_user
from ..services.result import retrieve_mypage_odaps


router = APIRouter(prefix="/mypage", tags=["Pull information for my page"])


@router.get("/odaps", response_model=List[ResultSetWithResult])
async def get_mypage_odaps(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return retrieve_mypage_odaps(current_user, db)


@router.get("/cbt_results")
async def get_mypage_cbt_results():
    return {"detail": "WIP"}
