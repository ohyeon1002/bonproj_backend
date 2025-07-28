from collections import defaultdict
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, Field
from ..schemas import UserSolvedQna, ManyResults, ResultsGot, OneResult
from ..models import Result, User
from ..crud.user_crud import read_one_user
from ..crud import result_crud, resultset_crud


def save_user_solved_qna(submitted_qna: UserSolvedQna, db: Session):
    is_correct = submitted_qna.answer == submitted_qna.choice
    new_result = Result(
        choice=submitted_qna.choice,
        correct=is_correct,
        gichulqna_id=submitted_qna.gichulqna_id,
        resultset_id=submitted_qna.odapset_id,
    )
    result_crud.create_one_result(new_result, db)
    db.commit()
    return new_result


def save_user_solved_many_qnas(results: ManyResults, current_user: User, db: Session):
    if results.duration_sec:
        resultset_to_update = resultset_crud.read_one_resultset(
            results.odapset_id, current_user.id, db
        )
        if resultset_to_update is None:
            raise HTTPException(status_code=404, detail="no such a resultset")
        resultset_to_update.duration_sec = results.duration_sec
        db.add(resultset_to_update)
    resultlist = [
        Result(
            choice=result.choice,
            correct=(result.choice == result.answer),
            gichulqna_id=result.gichulqna_id,
            resultset_id=results.odapset_id,
        )
        for result in results.results
    ]
    result_crud.create_many_results(resultlist, db)
    db.commit()
    return resultlist


def retrieve_many_user_saved_qnas(current_user: User, db: Session):
    assert current_user.id is not None
    resultsets = resultset_crud.read_many_resultsets(current_user.id, db)
    odaps_to_show = []
    for resultset in resultsets:
        if len(resultset.results) == 0:
            continue
        assert resultset.id and resultset.created_date is not None
        resultsgot = ResultsGot(
            resultset_id=resultset.id,
            created_date=resultset.created_date,
            exam_type=resultset.examtype,
            resultlist=[
                OneResult(choice=result.choice, gichulqna_id=result.gichulqna_id)
                for result in resultset.results
            ],
        )
        odaps_to_show.append(resultsgot)
    return odaps_to_show


def retrieve_mypage_odaps(current_user: User, db: Session):
    assert current_user.id is not None
    odapsets = resultset_crud.read_mypage_odaps_in_resultsets(current_user.id, db)
    return odapsets


def hide_saved_user_qna(id: int, current_user: User, db: Session):
    assert current_user.id is not None
    result_to_hide = result_crud.read_one_result_to_hide(id, current_user.id, db)
    if result_to_hide is None:
        raise HTTPException(status_code=404, detail="no such a result saved")
    result_to_hide.hidden = True
    db.add(result_to_hide)
    db.commit()
    return
