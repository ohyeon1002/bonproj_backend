from collections import defaultdict
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, Field
from ..schemas import UserSolvedQna, ManyResults, ResultsGot, OneResult
from ..models import Result, User
from ..crud.user_crud import read_one_user
from ..crud import result_crud, resultset_crud, gichulset_crud
from ..utils import result_utils
from ..utils.solve_utils import path_getter


def save_user_solved_qna(submitted_qna: UserSolvedQna, db: Session):
    print(submitted_qna.model_dump())
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


def save_user_solved_many_qnas(
    submitted_results: ManyResults, current_user: User, db: Session
):
    odapset_id = submitted_results.odapset_id
    resultset_to_update = resultset_crud.read_one_resultset(
        odapset_id, current_user.id, db
    )
    if resultset_to_update is None:
        raise HTTPException(status_code=404, detail="no such a resultset")
    resultset_to_update.duration_sec = submitted_results.duration_sec
    resultlist = [
        Result(
            choice=result.choice,
            correct=(result.choice == result.answer),
            gichulqna_id=result.gichulqna_id,
            resultset_id=odapset_id,
        )
        for result in submitted_results.results
    ]
    result_crud.create_many_results(resultlist, db)
    db.flush()
    db_resultset = resultset_crud.read_one_resultset_for_score(
        odapset_id, current_user.id, db
    )
    sample_gichulset_id, subject_scores = result_utils.score_answers(db_resultset)
    sample_gichulset_type = gichulset_crud.read_one_qna_set_type(
        sample_gichulset_id, db
    )
    total_amount, total_score, total_passed, final_subject_scores = (
        result_utils.check_if_passed(sample_gichulset_type, subject_scores)
    )
    db_resultset.total_amount = total_amount
    db_resultset.total_score = total_score
    db_resultset.passed = total_passed
    db.commit()
    return {
        "total_amount_of_questions": total_amount,
        "total_score_of_session": total_score,
        "if_passed_test": total_passed,
        "subject_scores": final_subject_scores,
    }


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
    unique_qnas = result_utils.leave_the_latest_qnas(odapsets)
    unique_qnas_with_imgPaths = result_utils.append_imgPaths(unique_qnas)
    return unique_qnas_with_imgPaths


def hide_saved_user_qna(id: int, current_user: User, db: Session):
    assert current_user.id is not None
    result_to_hide = result_crud.read_one_result_to_hide(id, current_user.id, db)
    if result_to_hide is None:
        raise HTTPException(status_code=404, detail="no such a result saved")
    result_to_hide.hidden = True
    db.add(result_to_hide)
    db.commit()
    return
