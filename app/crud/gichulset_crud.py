from typing import List
from sqlmodel import Session, select
from ..models import GichulSet, GichulSetType, GichulSetGrade


def read_qna_sets(
    license: GichulSetType,
    level: GichulSetGrade,
    db: Session,
):
    return db.exec(
        select(GichulSet).where(GichulSet.type == license, GichulSet.grade == level)
    ).all()


def read_one_qna_set_type(gichulset_id: int, db: Session):
    return db.exec(select(GichulSet.type).where(GichulSet.id == gichulset_id)).one
