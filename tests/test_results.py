save_one_url = "/api/results/save"


def test_save_one_201(solve_response, signed_client):
    odapset_id, gichulqna_id, answer = solve_response
    response = signed_client.post(
        save_one_url,
        json={
            "choice": "가",
            "gichulqna_id": gichulqna_id,
            "answer": answer,
            "odapset_id": odapset_id,
        },
    )
    assert response.status_code == 201


def test_save_one_404(solve_response, signed_client):
    """
    Emulate a request with a non-existing resultset_id.
    """
    _, gichulqna_id, answer = solve_response
    response = signed_client.post(
        save_one_url,
        json={
            "choice": "가",
            "gichulqna_id": gichulqna_id,
            "answer": answer,
            "odapset_id": 0,  # fail
        },
    )
    assert response.status_code == 404
    assert str(response.json()["detail"]).startswith("Resultset with")


def test_save_one_422(solve_response, signed_client):
    """
    Emulate a request that fails the schema validation by sending "다" as a choice when it has to be one of "가", "나", "사", or "아".
    """
    odapset_id, gichulqna_id, answer = solve_response
    response = signed_client.post(
        save_one_url,
        json={
            "choice": "다",  # fail
            "gichulqna_id": gichulqna_id,
            "answer": answer,
            "odapset_id": odapset_id,
        },
    )
    assert response.status_code == 422


save_many_url = "/api/results/savemany"


def test_save_many_201(solve_response, signed_client):
    odapset_id, _, _ = solve_response
    response = signed_client.post(
        save_many_url,
        json={
            "odapset_id": odapset_id,
            "duration_sec": 3600,
            "results": [
                {"choice": "아", "answer": "아", "gichulqna_id": 1},
                {"choice": "가", "answer": "가", "gichulqna_id": 2},
                {"choice": "나", "answer": "아", "gichulqna_id": 3},
                {"choice": "사", "answer": "나", "gichulqna_id": 4},
                {"choice": "아", "answer": "아", "gichulqna_id": 5},
                {"choice": "가", "answer": "가", "gichulqna_id": 6},
                {"choice": "나", "answer": "나", "gichulqna_id": 7},
                {"choice": "가", "answer": "아", "gichulqna_id": 8},
                {"choice": "아", "answer": "아", "gichulqna_id": 9},
                {"choice": "사", "answer": "가", "gichulqna_id": 10},
            ],
        },
    )
    assert response.status_code == 201
    response_data = response.json()
    required_keys = {
        "exam_detail",
        "duration_sec",
        "total_amount_of_questions",
        "total_correct_counts",
        "total_score",
        "if_passed_test",
        "subject_scores",
    }
    assert required_keys == response_data.keys()
    subject_score_keys = {
        "question_counts",
        "correct_counts",
        "passed",
    }
    assert subject_score_keys == response_data["subject_scores"]["항해"].keys()


def test_save_many_404(signed_client):
    response = signed_client.post(
        save_many_url,
        json={
            "odapset_id": 0,  # fail
            "duration_sec": 3600,
            "results": [
                {"choice": "아", "answer": "아", "gichulqna_id": 1},
                {"choice": "가", "answer": "가", "gichulqna_id": 2},
                {"choice": "나", "answer": "아", "gichulqna_id": 3},
                {"choice": "사", "answer": "나", "gichulqna_id": 4},
                {"choice": "아", "answer": "아", "gichulqna_id": 5},
                {"choice": "가", "answer": "가", "gichulqna_id": 6},
                {"choice": "나", "answer": "나", "gichulqna_id": 7},
                {"choice": "가", "answer": "아", "gichulqna_id": 8},
                {"choice": "아", "answer": "아", "gichulqna_id": 9},
                {"choice": "사", "answer": "가", "gichulqna_id": 10},
            ],
        },
    )
    assert response.status_code == 404
    assert str(response.json()["detail"]).startswith("Resultset with")


def test_save_many_422(solve_response, signed_client):
    odapset_id, _, _ = solve_response
    response = signed_client.post(
        save_many_url,
        json={
            "odapset_id": odapset_id,
            "duration_sec": 3600,
            "results": [
                {"choice": "다", "answer": "아", "gichulqna_id": 1},  # fail
                {"choice": "가", "answer": "가", "gichulqna_id": 2},
                {"choice": "나", "answer": "아", "gichulqna_id": 3},
                {"choice": "사", "answer": "나", "gichulqna_id": 4},
                {"choice": "아", "answer": "아", "gichulqna_id": 5},
                {"choice": "가", "answer": "가", "gichulqna_id": 6},
                {"choice": "나", "answer": "나", "gichulqna_id": 7},
                {"choice": "가", "answer": "아", "gichulqna_id": 8},
                {"choice": "아", "answer": "아", "gichulqna_id": 9},
                {"choice": "사", "answer": "가", "gichulqna_id": 10},
            ],
        },
    )
    assert response.status_code == 422


def test_soft_delete_one_204(save_one_and_get_mypage_response, signed_client):
    result_id = save_one_and_get_mypage_response
    response = signed_client.delete(f"/api/results/{result_id}")
    assert response.status_code == 204


def test_soft_delete_one_422(signed_client):
    response = signed_client.delete("/api/results/a_string")
    assert response.status_code == 422


def test_get_test_result_200(save_many_and_get_mypage_exam_response, signed_client):
    resultset_id = save_many_and_get_mypage_exam_response
    response = signed_client.get(f"/api/results/{resultset_id}")
    assert response.status_code == 200
    required_keys = {
        "id",
        "examtype",
        "created_date",
        "duration_sec",
        "total_amount",
        "total_score",
        "passed",
        "results",
    }
    response_data = response.json()
    assert required_keys == response_data.keys()
    assert response_data["examtype"] == "exam"
    results_required_keys = {"id", "choice", "correct", "gichul_qna"}
    assert results_required_keys == response_data["results"][0].keys()
    gichulqna_required_keys = {
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
    }
    assert gichulqna_required_keys == response_data["results"][0]["gichul_qna"].keys()


def test_get_test_result_404(save_many_and_get_mypage_exam_response, signed_client):
    response = signed_client.get("/api/results/0")  # fail
    assert response.status_code == 404


def test_get_test_result_422(signed_client):
    response = signed_client.get("/api/results/a_string")  # fail
    assert response.status_code == 422
