from collections import defaultdict
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, Field
from ..schemas import UserSolvedQna, ManyOdaps, OdapsGot, OneOdap
from ..models import Odap, User
from ..crud.user_crud import read_one_user
from ..crud import odap_crud, odapset_crud


def save_user_solved_qna(odap_data: UserSolvedQna, current_user: User, db: Session):
    user = read_one_user(current_user.username, db)
    if user is None:
        raise HTTPException(
            status_code=401, detail="This feature is only for singned users"
        )
    new_odap = Odap(
        choice=odap_data.choice,
        gichulqna_id=odap_data.gichulqna_id,
        odapset_id=odap_data.odapset_id,
    )
    try:
        odap_crud.create_one_odap(new_odap, db)
        db.commit()
        db.refresh(new_odap)
    except:
        db.rollback()
        raise HTTPException(status_code=404)
    return new_odap


def save_user_solved_many_qnas(odaps: ManyOdaps, current_user: User, db: Session):
    try:
        user = read_one_user(current_user.username, db)
        if user is None:
            raise HTTPException(
                status_code=401, detail="This feature is only for singned users"
            )
        odaplist = [
            Odap(
                choice=odap.choice,
                gichulqna_id=odap.gichulqna_id,
                odapset_id=odaps.odapset_id,
            )
            for odap in odaps.odaps
        ]
        odap_crud.create_many_odaps(odaplist, db)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(404)
    return odaps


def retrieve_many_user_saved_qnas(current_user: User, db: Session):
    assert current_user.id is not None
    odapsets = odapset_crud.read_many_odapsets(current_user.id, db)
    odaps_to_show = []
    for odapset in odapsets:
        if len(odapset.odaps) == 0:
            continue
        assert odapset.id and odapset.created_date is not None
        odapsgot = OdapsGot(
            odapset_id=odapset.id,
            created_date=odapset.created_date,
            exam_type=odapset.examtype,
            odaplist=[
                OneOdap(choice=odap.choice, gichulqna_id=odap.gichulqna_id)
                for odap in odapset.odaps
            ],
        )
        odaps_to_show.append(odapsgot)
    return odaps_to_show


#  {
#     id: 4,
#     subject: "영어",
#     gichulqna_id: 104,
#     odapset_id: 1,
#     created_at: "2024-07-04T13:00:00Z",
#     choice: "가",
#     question: "다음 중 영어로 올바른 표현은?",
#     choices: [
#       { label: "가", text: "How are you?" },
#       { label: "나", text: "How is you?" },
#       { label: "다", text: "How be you?" },
#       { label: "라", text: "How are she?" },
#     ],
#     answer: "가",
#     explanation: "How are you?가 올바른 표현입니다.",
#     count: 1,
#   },


def retrieve_mypage_odaps(current_user: User, db: Session):
    assert current_user.id is not None
    odapsets = odapset_crud.read_mypage_odapsets(current_user.id, db)
    return odapsets
