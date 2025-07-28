from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, Field, select
from sqlalchemy.orm import selectinload
from ..schemas import UserSolvedQna, UserBase, ManyResults
from ..models import Result, User, ResultSet, ExamType
from .user_crud import read_one_user


def create_one_result(new_result: Result, db: Session):
    db.add(new_result)
    return new_result


def create_many_results(resultlist: List[Result], db: Session):
    db.add_all(resultlist)
    return resultlist


def read_one_result_to_hide(id: int, user_id: int, db: Session):
    result_read = db.exec(
        select(Result)
        .where(Result.id == id, Result.resultset.has(ResultSet.user_id == user_id))
        .order_by(Result.id.desc())
    ).first()
    return result_read
