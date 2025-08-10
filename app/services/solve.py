from typing import Literal, Optional
from sqlmodel import Session
from fastapi import HTTPException, status
from ..models import GichulSetType, GichulSetInning, GichulSetGrade, ExamType, User
from ..utils import solve_utils
from ..crud import resultset_crud, solve_crud
from ..schemas import SolveResponse, QnaWithImgPaths


def retrieve_one_inning(
    examtype: ExamType,
    year: Literal["2021", "2022", "2023"],
    license: GichulSetType,
    level: GichulSetGrade,
    round: GichulSetInning,
    db: Session,
    current_user: Optional[User],
) -> SolveResponse:
    gichulset = solve_crud.get_one_inning(year, license, level, round, db)
    if gichulset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="검색 실패: 기출 문제 없음"
        )

    # 경로 정보 생성
    directory = solve_utils.dir_maker(year, license, level, round)
    path_dict = solve_utils.path_getter(directory)
    path_cache = {gichulset.id: path_dict}

    # 문제 목록을 딕셔너리로 변환 후 이미지 경로 추가
    qnas_as_dicts = [qna.model_dump() for qna in gichulset.qnas]
    new_qnas_list = solve_utils.attach_image_paths(qnas_as_dicts, path_cache)

    pdt_validated_list = [
        QnaWithImgPaths.model_validate(qna_dict) for qna_dict in new_qnas_list
    ]
    if current_user is None:
        return SolveResponse(qnas=pdt_validated_list)
    new_resultset = resultset_crud.create_one_resultset(examtype, current_user.id, db)
    return SolveResponse(odapset_id=new_resultset.id, qnas=pdt_validated_list)
