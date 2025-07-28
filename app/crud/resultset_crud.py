from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, Field, select
from sqlalchemy.orm import selectinload
from ..schemas import UserSolvedQna, UserBase
from ..models import User, ResultSet, ExamType, Result, GichulQna
from .user_crud import read_one_user


def create_one_resultset(examtype: str, user_id: int, db: Session):
    new_resultset = ResultSet(examtype=ExamType(examtype), user_id=user_id)
    db.add(new_resultset)
    db.commit()
    db.refresh(new_resultset)
    return new_resultset


def read_one_resultset(resultset_id: int, user_id: int, db: Session):
    statement = select(ResultSet).where(
        ResultSet.id == resultset_id, ResultSet.user_id == user_id
    )
    resultset_to_update = db.exec(statement).one_or_none()
    return resultset_to_update


def read_many_resultsets(user_id: int, db: Session):
    return db.exec(select(ResultSet).where(ResultSet.user_id == user_id)).all()


def read_mypage_odaps_in_resultsets(user_id: int, db: Session):
    statement = (
        select(ResultSet)
        .where(ResultSet.user_id == user_id, ResultSet.results.any())
        .options(selectinload(ResultSet.results).selectinload(Result.gichul_qna))
        .order_by(ResultSet.id.desc())
    )
    odap_sets = db.exec(statement).all()
    return odap_sets
