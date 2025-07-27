from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, Field, select
from sqlalchemy.orm import selectinload
from ..schemas import UserSolvedQna, UserBase
from ..models import User, OdapSet, ExamType, Odap, GichulQna
from .user_crud import read_one_user


def create_one_odapset(examtype: str, user_id: int, db: Session):
    new_odapset = OdapSet(examtype=ExamType(examtype), user_id=user_id)
    db.add(new_odapset)
    db.commit()
    db.refresh(new_odapset)
    return new_odapset


def read_many_odapsets(user_id: int, db: Session):
    return db.exec(select(OdapSet).where(OdapSet.user_id == user_id)).all()


def read_mypage_odapsets(user_id: int, db: Session):
    statement = (
        select(OdapSet)
        .join(Odap)
        .where(OdapSet.user_id == user_id)
        .options(selectinload(OdapSet.odaps).selectinload(Odap.gichul_qna))
        .order_by(OdapSet.id.desc())
        .distinct()
    )
    odap_sets = db.exec(statement).all()
    return odap_sets
