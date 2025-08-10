import re, random
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from collections import defaultdict
from ..dependencies import get_optional_current_activate_user
from ..core.config import settings
from ..utils import solve_utils
from ..schemas import CBTResponse
from ..database import get_db
from ..models import (
    ExamType,
    ResultSet,
    User,
    GichulSet,
    GichulSetGrade,
    GichulSetType,
    GichulSubject,
)

router = APIRouter(prefix="/cbt", tags=["Randomly Mixed Questions"])


@router.get("/")
def get_one_random_qna_set(
    license: GichulSetType,
    level: GichulSetGrade,
    *,
    subjects: List[GichulSubject] = Query(),
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_optional_current_activate_user)],
):
    try:
        # 1. 모든 기출 세트(GichulSet)를 가져옵니다.
        sets = db.exec(
            select(GichulSet).where(GichulSet.type == license, GichulSet.grade == level)
        ).all()

        # 2. 모든 세트에 대한 이미지 경로를 미리 캐싱합니다.
        path_cache = {}
        for s in sets:
            directory = solve_utils.dir_maker(str(s.year), s.type, s.grade, s.inning)
            path_cache[s.id] = solve_utils.path_getter(directory)

        # 3. 중복되지 않는 모든 문제를 수집합니다.
        dic = defaultdict(list)
        for s in sets:
            for qna in s.qnas:
                if qna.questionstr and qna.ex1str:
                    # 간단한 중복 제거 로직
                    joined_text = " ".join([qna.questionstr, qna.ex1str])
                    if joined_text not in dic[qna.subject]:
                        dic[qna.subject].append(qna)

        # 4. 과목별로 문제를 랜덤 샘플링하고 이미지 경로를 추가합니다.
        random_set = defaultdict()
        for subject in subjects:
            random_qnas = random.sample(dic[subject], 25)
            qnas_as_dicts = [qna.model_dump() for qna in random_qnas]

            # 중앙 유틸리티 함수 호출
            qnas_with_paths = solve_utils.attach_image_paths(qnas_as_dicts, path_cache)

            for idx, qna_dict in enumerate(qnas_with_paths):
                qna_dict["qnum"] = idx + 1

            random_set[subject] = qnas_with_paths

        # 5. 최종 응답을 생성합니다.
        if current_user is None:
            return CBTResponse(subjects=random_set)

        new_resultset = ResultSet(examtype=ExamType.cbt, user_id=current_user.id)
        db.add(new_resultset)
        db.commit()
        db.refresh(new_resultset)
        return CBTResponse(odapset_id=new_resultset.id, subjects=random_set)

    except ValueError as e:
        raise HTTPException(status_code=404, detail="과목을 잘못 선택하셨습니다.")
