from typing import List, Optional, Sequence, Tuple
from sqlmodel import Session, select
from ..models import GichulQna, GichulSubject


def read_correct_answers(
    gichulqna_id_list: List[int], db: Session
) -> Sequence[Tuple[int, GichulSubject, str]]:
    statement = select(GichulQna.id, GichulQna.subject, GichulQna.answer).where(
        GichulQna.id.in_(gichulqna_id_list)
    )
    correct_answers = db.exec(statement).all()
    return correct_answers
