from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..models import User
from ..schemas import ResultSetWithResult
from ..database import get_db
from ..dependencies import get_current_active_user
from ..services.result import retrieve_mypage_odaps, retrieve_session_resultsets


router = APIRouter(prefix="/mypage", tags=["Pull information for my page"])


@router.get("/odaps")
async def get_mypage_odaps(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return retrieve_mypage_odaps(current_user, db)


@router.get("/cbt_results")
async def get_mypage_cbt_results(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return retrieve_session_resultsets(current_user, db, is_cbt=True)


@router.get("/exam_results")
def get_mypage_exam_results(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return retrieve_session_resultsets(current_user, db, is_cbt=False)
