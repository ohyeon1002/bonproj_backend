odaps_url = "/api/mypage/odaps"


def test_get_odaps_200(save_many_and_get_mypage_exam_response, signed_client):
    response = signed_client.get(odaps_url)
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    required_keys = {
        "id",
        "subject",
        "qnum",
        "questionstr",
        "ex1str",
        "ex2str",
        "ex3str",
        "ex4str",
        "answer",
        "explanation",
        "gichulset_id",
        "gichulset",
        "choice",
        "result_id",
        "hidden",
        "attempt_counts",
    }
    assert required_keys == response_data[0].keys()
    required_gichulset_keys = {"year", "type", "grade", "inning"}
    assert required_gichulset_keys == response_data[0]["gichulset"].keys()


cbt_url = "/api/mypage/cbt_results"


def test_mypage_cbt_200(get_cbt_and_save_many, signed_client):
    response = signed_client.get(cbt_url)
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    required_keys = {
        "resultset_id",
        "duration_sec",
        "exam_detail",
        "total_amount_of_questions",
        "total_correct_counts",
        "total_score",
        "if_passed_test",
        "subject_scores",
    }
    assert required_keys == response_data[0].keys()
    subject_scores_data = response_data[0]["subject_scores"]
    assert isinstance(subject_scores_data, dict)
    required_subject_keys = {
        "question_counts",
        "correct_counts",
        "passed",
    }
    for subject_data in subject_scores_data.values():
        assert required_subject_keys == subject_data.keys()


mypage_exam_url = "/api/mypage/exam_results"


def test_mypage_exam_200(save_many_and_get_mypage_exam_response, signed_client):
    response = signed_client.get(mypage_exam_url)
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    required_keys = {
        "resultset_id",
        "duration_sec",
        "exam_detail",
        "total_amount_of_questions",
        "total_correct_counts",
        "total_score",
        "if_passed_test",
        "subject_scores",
    }
    assert required_keys == response_data[0].keys()
    subject_scores_data = response_data[0]["subject_scores"]
    assert isinstance(subject_scores_data, dict)
    required_subject_keys = {
        "question_counts",
        "correct_counts",
        "passed",
    }
    for subject_data in subject_scores_data.values():
        assert required_subject_keys == subject_data.keys()
