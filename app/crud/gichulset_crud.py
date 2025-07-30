from typing import Collection
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


def read_one_qna_set(gichulset_id: int, db: Session):
    return db.exec(select(GichulSet).where(GichulSet.id == gichulset_id)).one()


def read_many_gichulset_by_ids(gichulset_ids: Collection[int], db: Session):
    return db.exec(select(GichulSet).where(GichulSet.id.in_(gichulset_ids))).all()
