cbt_url = "/api/cbt"
cbt_params_successful = {
    "license": "항해사",
    "level": "1",
    "subjects": ["항해", "운용", "영어"],
}


def test_get_one_random_qna_set_unsigned_200(client):
    response = client.get(cbt_url, params=cbt_params_successful)
    assert response.status_code == 200
    response_data = response.json()
    assert "odapset_id" in response_data
    assert response_data["odapset_id"] is None
    assert "subjects" in response_data
    assert "항해" in response_data["subjects"]
    assert isinstance(response_data["subjects"]["항해"], list)
    assert any(qna["imgPaths"] for qna in response_data["subjects"]["영어"])


def test_get_one_random_qna_set_unsigned_404(client):
    """
    Emulate sending the wrong parameter "직무일반" as a subject.
    """
    response = client.get(
        cbt_url,
        params={
            "license": "항해사",
            "level": "1",
            "subjects": ["항해", "운용", "직무일반"],  # fail
        },
    )
    assert response.status_code == 404


def test_get_one_random_qna_set_signed_200(signed_client):
    """
    Emulate a request from a signed user to see if it successfully returns odapset_id.
    """
    response = signed_client.get(cbt_url, params=cbt_params_successful)
    assert response.status_code == 200
    response_data = response.json()
    assert "odapset_id" in response_data
    assert response_data["odapset_id"] is not None
