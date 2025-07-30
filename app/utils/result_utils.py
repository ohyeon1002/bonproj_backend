import re
from collections import defaultdict
from typing import Sequence, Tuple, List, Dict, Union, Any, Optional
from ..models import GichulSubject, ResultSet, GichulSetType
from ..schemas import ManyResults, ResultSetWithResult, ResultSetResponse
from .solve_utils import dir_maker, path_getter


def check_if_passed(
    sample_gichulset_type: GichulSetType,
    subject_scores=Dict[Any, Dict[str, Union[int, bool]]],
):
    # defaultdict({<GichulSubject.hanghae: '항해'>: {'question_counts': 25, 'correct_counts': 4}, <GichulSubject.unyong: '운용'>: {'question_counts': 25, 'correct_counts': 0}, <GichulSubject.beopgyu: '법규'>: {'question_counts': 25, 'correct_counts': 1}, <GichulSubject.english: '영어'>: {'question_counts': 25, 'correct_counts': 0}, <GichulSubject.sangseon: '상선전문'>: {'question_counts': 25, 'correct_counts': 0}})
    data = [
        (value_dict["question_counts"], value_dict["correct_counts"])
        for value_dict in subject_scores.values()
    ]
    total_amount, total_score = tuple(sum(group) for group in zip(*data))
    for subject, contents in subject_scores.items():
        if (
            sample_gichulset_type == GichulSetType.hanghaesa
            and subject == GichulSubject.beopgyu
        ):
            contents["passed"] = contents["correct_counts"] >= 15
        else:
            contents["passed"] = contents["correct_counts"] >= 10
    passed = True
    if any(not v["passed"] for v in subject_scores.values()):
        passed = False
    elif total_score / len(subject_scores) < 15:
        passed = False
    return total_amount, total_score, passed, subject_scores


def score_answers(
    resultset: ResultSet, is_used_in_mypage: bool = None
) -> Tuple[Optional[int], Dict[Any, Dict[str, Union[int, bool]]]]:
    resultset_dict = ResultSetResponse.model_validate(resultset).model_dump()
    if not is_used_in_mypage:
        sample_gichulset_id: int = resultset_dict["results"][0]["gichul_qna"][
            "gichulset_id"
        ]
    subject_scores = defaultdict(
        lambda: {"question_counts": 0, "correct_counts": 0, "passed": False}
    )
    for result in resultset_dict["results"]:
        result_subject = result["gichul_qna"]["subject"]
        subject_scores[result_subject]["question_counts"] += 1
        if result["correct"]:
            subject_scores[result_subject]["correct_counts"] += 1
    if is_used_in_mypage:
        return subject_scores
    return sample_gichulset_id, subject_scores


def leave_the_latest_qnas(
    odapsets: Sequence[ResultSet],
) -> List[Dict[str, Union[str, int, Dict[str, Union[str, int]]]]]:
    odapsets_data = [
        ResultSetWithResult.model_validate(odapset).model_dump() for odapset in odapsets
    ]
    unique_qnas = {}
    attempts_counts = defaultdict(int)
    for odapset_dict in odapsets_data:
        for result_dict in odapset_dict["results"]:
            if result_dict["hidden"] or result_dict["correct"]:
                continue
            if not result_dict["choice"]:
                continue
            qna_dict = result_dict["gichul_qna"]
            qna_id = qna_dict["id"]
            attempts_counts[qna_id] += 1
            if qna_id not in unique_qnas:
                unique_qnas[qna_id] = qna_dict
                unique_qnas[qna_id]["choice"] = result_dict["choice"]
                unique_qnas[qna_id]["result_id"] = result_dict["id"]
                unique_qnas[qna_id]["hidden"] = result_dict["hidden"]
    return [
        {**qna_dict, "attempt_counts": attempts_counts[qna_id]}
        for qna_id, qna_dict in unique_qnas.items()
    ]


def append_imgPaths(unique_qnas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    path_cache = {}
    pic_marker_reg = re.compile(r"@(\w+)")  # '@'를 제외한 'pic123' 같은 부분만 캡처

    for qna_dict in unique_qnas:
        full_text = " ".join(
            str(qna_dict.get(key, ""))
            for key in [
                "questionstr",
                "ex1str",
                "ex2str",
                "ex3str",
                "ex4str",
            ]
        )

        # found_pic_markers 결과: ['pic123', 'pic456'] ('@' 없음)
        found_pic_markers = pic_marker_reg.findall(full_text)

        if not found_pic_markers:
            continue

        gichulset_id = qna_dict.get("gichulset_id")
        if not gichulset_id:
            continue

        if gichulset_id not in path_cache:
            gichulset_info = qna_dict.get("gichulset")
            directory = dir_maker(
                year=gichulset_info["year"],
                license=gichulset_info["type"],
                level=gichulset_info["grade"],
                round=gichulset_info["inning"],
            )
            path_cache[gichulset_id] = path_getter(directory)

        # image_map_for_set의 키는 'pic123' 형태입니다. (예: {'pic123': 'path/to/img.png'})
        image_map_for_set = path_cache[gichulset_id]

        img_paths = []
        # ★★★ 가장 중요한 변경점 ★★★
        # found_pic_markers의 각 요소('pic123')를 그대로 키로 사용합니다.
        for marker in found_pic_markers:
            if marker in image_map_for_set:
                img_paths.append(image_map_for_set[marker])

        if img_paths:
            # 중복된 이미지 경로를 제거하고 싶다면 set을 활용할 수 있습니다.
            qna_dict["imgPaths"] = sorted(list(set(img_paths)))
        else:
            # 이미지 경로를 찾지 못한 경우 빈 리스트를 명시적으로 추가할 수 있습니다.
            qna_dict["imgPaths"] = []

    return unique_qnas
