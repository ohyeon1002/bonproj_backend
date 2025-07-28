from collections import defaultdict
from typing import Sequence, Tuple
from ..models import GichulSubject
from ..schemas import ManyResults


def score_answers(
    submitted_qnas: ManyResults,
    correct_answer: Sequence[Tuple[int, GichulSubject, str]],
):
    correct_answer_dict = {
        qna_id: (subject, answer) for qna_id, subject, answer in correct_answer
    }
    subject_scores = defaultdict(lambda: {"total": 0, "correct": 0})
    for user_answer in submitted_qnas.results:
        subject, right_answer = correct_answer_dict[user_answer.gichulqna_id]
        subject_scores[subject]["total"] += 1
        if right_answer == user_answer.choice:
            subject_scores[subject]["correct"] += 1
    return subject_scores
