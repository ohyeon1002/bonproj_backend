import re
from collections import defaultdict
from typing import Sequence, Tuple, List, Dict, Union, Any, Optional
from ..models import GichulSubject, ResultSet, GichulSetType
from ..schemas import ManyResults, ResultSetWithResult, ResultSetResponse
from .solve_utils import dir_maker, path_getter, attach_image_paths


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
    qna_to_gichulset_map = {}
    for odapset in odapsets:
        for result in odapset.results:
            if result.gichul_qna and result.gichul_qna.gichulset:
                qna_to_gichulset_map[result.gichul_qna.id] = result.gichul_qna.gichulset
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
                if qna_id in qna_to_gichulset_map:
                    gichulset = qna_to_gichulset_map[qna_id]
                    unique_qnas[qna_id]["gichulset"] = {
                        "year": gichulset.year,
                        "type": gichulset.type,
                        "grade": gichulset.grade,
                        "inning": gichulset.inning,
                    }
                unique_qnas[qna_id]["choice"] = result_dict["choice"]
                unique_qnas[qna_id]["result_id"] = result_dict["id"]
                unique_qnas[qna_id]["hidden"] = result_dict["hidden"]
    return [
        {**qna_dict, "attempt_counts": attempts_counts[qna_id]}
        for qna_id, qna_dict in unique_qnas.items()
    ]


def append_imgPaths(unique_qnas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    path_cache = {}
    for qna_dict in unique_qnas:
        gichulset = qna_dict.get("gichulset")
        if not gichulset:
            continue

        gichulset_id = gichulset.get("id")
        if gichulset_id and gichulset_id not in path_cache:
            directory = dir_maker(
                year=str(gichulset["year"]),
                license=gichulset["type"],
                level=gichulset["grade"],
                round=gichulset["inning"],
            )
            path_cache[gichulset_id] = path_getter(directory)

    return attach_image_paths(unique_qnas, path_cache)
