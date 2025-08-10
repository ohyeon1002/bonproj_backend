from typing import Dict, Any, List
from ..core.config import settings
from ..models import (
    GichulQna,
    GichulSetType,
    GichulSetInning,
    GichulSetGrade,
)
import re


def dir_maker(
    year: str, license: GichulSetType, level: GichulSetGrade, round: GichulSetInning
) -> str:
    esd = ""
    if license == GichulSetType.gigwansa:
        esd = "E"
    elif license == GichulSetType.hanghaesa:
        esd = "D"
    elif license == GichulSetType.sohyeong:
        esd = "S"

    grd = level.value
    if level == GichulSetGrade.grade_none:
        grd = GichulSetGrade.grade_1.value

    inn = round.value

    dir_path = f"{license.value}/{esd}{grd}_{year}_0{inn}"
    return dir_path


def path_getter(directory: str) -> Dict[str, str]:
    base_path = settings.BASE_PATH
    path_to_search = base_path / directory
    png_files = list(path_to_search.glob("*.png"))
    path_dict = {}
    for p in png_files:
        file_stem = p.stem
        try:
            lookup_key = file_stem.split("-")[-1]
        except IndexError:
            print("split didn't work; additional work needed")
            continue  # '-'로 분리되지 않으면 건너뛰기
        rel_path = p.relative_to(base_path).as_posix()
        path_dict[lookup_key] = rel_path
    return path_dict


def attach_image_paths(
    qna_dicts: List[Dict], path_cache: Dict[int, Dict[str, str]]
) -> List[Dict[str, Any]]:
    pic_marker_reg = re.compile(r"@(\w+)")

    for qna_dict in qna_dicts:
        gichulset_id = qna_dict.get("gichulset_id")
        if not gichulset_id or gichulset_id not in path_cache:
            continue

        image_map_for_set = path_cache[gichulset_id]
        full_text = " ".join(
            str(qna_dict.get(key, ""))
            for key in ["questionstr", "ex1str", "ex2str", "ex3str", "ex4str"]
        )
        found_pic_markers = pic_marker_reg.findall(full_text)

        if found_pic_markers:
            img_paths = [
                image_map_for_set[marker.lower()]
                for marker in found_pic_markers
                if marker.lower() in image_map_for_set
            ]
            if img_paths:
                qna_dict["imgPaths"] = sorted(list(set(img_paths)))

    return qna_dicts
