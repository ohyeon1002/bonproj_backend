import sys
import os

# --- 프로젝트 설정 (기존과 동일) ---
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import json
import re
from pathlib import Path
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from app.core.config import settings
from app.database import engine
from app.models import (
    GichulSet,
    GichulQna,
    GichulSetType,
    GichulSetInning,
    GichulSetGrade,
    GichulSubject,
)


# --- 정규화 함수 (기존과 동일) ---
def normalize_gichulset_name(name: str) -> tuple[str, str]:
    normalized_type = ""
    if "기관사" in name:
        normalized_type = "기관사"
    elif "항해사" in name:
        normalized_type = "항해사"
    elif "소형" in name:
        normalized_type = "소형선박조종사"
        return (normalized_type, "0")
    else:
        pass
    split = re.split(r"[\s.]+", name)
    if len(split) > 1:
        grade = split[1].rstrip("급")
        return (normalized_type, grade)
    return (normalized_type, "")


# --- 과목명 정규화 함수 (데이터 삽입 시 사용했던 함수) ---
def normalize_gichulqna_qsub(qsub: str) -> str:
    """ "1. 항해" 같은 문자열에서 "항해"만 추출합니다."""
    split = re.split(r"[\.\s?]", qsub)
    return split[-1]


# --- 복합 키를 사용하도록 수정한 최종 업데이트 함수 ---
def update_json_with_explanations_final(session: Session, json_file_path: Path):
    """
    (과목, 문제번호) 복합 키를 사용하여 정확하게 해설을 매핑합니다.
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    subject_info = data["subject"]

    settype, grade = normalize_gichulset_name(subject_info["name"])
    year = int(subject_info["year"])
    inning = str(subject_info["inning"])

    statement = (
        select(GichulSet)
        .options(selectinload(GichulSet.qnas))
        .where(
            GichulSet.type == GichulSetType(settype),
            GichulSet.grade == GichulSetGrade(grade),
            GichulSet.year == year,
            GichulSet.inning == GichulSetInning(inning),
        )
    )
    gichulset = session.exec(statement).first()

    if not gichulset or not gichulset.qnas:
        print(
            f"  [정보] DB에서 일치하는 문제 세트를 찾을 수 없음: {json_file_path.name}"
        )
        return

    # --- 변경점 1: (과목, 문제번호)를 복합 키로 사용하는 딕셔너리 생성 ---
    # qna.subject는 Enum 객체이므로 .value로 실제 문자열 값을 가져옵니다.
    explanations_map = {
        (qna.subject.value, qna.qnum): qna.explanation
        for qna in gichulset.qnas
        if qna.explanation and qna.explanation.strip()
    }

    if not explanations_map:
        print(f"  [정보] DB에 추가할 해설 데이터가 없음: {json_file_path.name}")
        return

    is_updated = False
    # --- 변경점 2: JSON을 순회하며 복합 키로 해설 조회 ---
    for subject_group in subject_info["type"]:
        # JSON의 과목명("1. 항해")을 DB와 동일한 형식("항해")으로 정규화합니다.
        current_subject = normalize_gichulqna_qsub(subject_group["string"])

        for q in subject_group["questions"]:
            q_num = int(q["num"])

            # (과목, 문제번호) 튜플을 조회 키로 사용합니다.
            lookup_key = (current_subject, q_num)

            if lookup_key in explanations_map:
                q["explanation"] = explanations_map[lookup_key]
                is_updated = True

    if is_updated:
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"  [성공] 파일 업데이트 완료: {json_file_path.name}")
    else:
        print(f"  [정보] 업데이트할 내용이 없음: {json_file_path.name}")


# --- 메인 실행 블록 ---
if __name__ == "__main__":
    print("JSON 파일에 DB의 해설 데이터를 추가하는 최종 스크립트를 시작합니다.")
    path = settings.BASE_PATH

    with Session(engine) as session:
        for questionfolder in path.glob("*/*"):
            json_file_path = questionfolder / f"{questionfolder.name}.json"
            if not json_file_path.exists():
                continue

            print(f"처리 시작: {json_file_path.relative_to(path)}")
            try:
                # 최종 수정된 함수 호출
                update_json_with_explanations_final(session, json_file_path)
            except Exception as e:
                print(f"  [오류] 처리 중 예외 발생: {e} at {json_file_path.name}")

    print("\n모든 작업이 완료되었습니다.")
