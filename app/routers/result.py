from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from ..schemas import UserSolvedQna, ManyResults, ResultSetResponse
from ..dependencies import get_current_active_user
from ..database import get_db
from ..services.result import (
    save_user_solved_qna,
    save_user_solved_many_qnas,
    retrieve_many_user_saved_qnas,
    hide_saved_user_qna,
)
from ..models import Result, User
from ..crud.resultset_crud import read_one_resultset_for_score


router = APIRouter(prefix="/results", tags=["Save user-solved qnas"])


@router.post("/save", status_code=201)
async def save_one_qna(
    submitted_qna: UserSolvedQna,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return save_user_solved_qna(submitted_qna, current_user, db)


@router.post("/savemany", status_code=201)
async def save_many_qnas(
    submitted_qnas: ManyResults,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return save_user_solved_many_qnas(submitted_qnas, current_user, db)


@router.delete("/{result_id}", status_code=204)
async def soft_delete_one_result(
    result_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return hide_saved_user_qna(result_id, current_user, db)


@router.get("/{resultset_id}", response_model=ResultSetResponse)
def get_test_result_details(
    resultset_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    resultset = read_one_resultset_for_score(resultset_id, current_user.id, db)
    if not resultset:
        raise HTTPException(
            status_code=404, detail=f"Resultset with id = {resultset_id} not found"
        )
    return resultset


# @router.get("/odaplist")
async def get_many_odaps(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    odaps_to_show = retrieve_many_user_saved_qnas(current_user, db)
    return odaps_to_show
