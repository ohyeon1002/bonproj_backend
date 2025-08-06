solve_params_successful = {
    "examtype": "practice",
    "year": "2021",
    "license": "항해사",
    "level": "1",
    "round": "1",
}


def test_get_one_inning_unsigned_200(client):
    response = client.get(
        "/api/solve/",
        params=solve_params_successful,
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "qnas" in response_data
    assert "imgPaths" in response_data["qnas"][0]
    assert response_data["qnas"][96]["imgPaths"] is not None
    assert isinstance(response_data["qnas"], list)
    assert len(response_data["qnas"]) > 0


def test_get_one_inning_unsgined_404(client):
    """
    Emulate a request for a question set that doesn't exist.
    """
    response = client.get(
        "/api/solve/",
        params={
            "examtype": "practice",
            "year": "2021",
            "license": "항해사",
            "level": "0",  # fail
            "round": "1",
        },
    )

    assert response.status_code == 404


def test_get_one_inning_unsgined_422(client):
    """
    Emulate a parameter validation failure by pydantic, which sends 2025 when it has to be one of 2021, 2022, or 2023.
    """
    response = client.get(
        "/api/solve/",
        params={
            "examtype": "practice",
            "year": "2025",  # fail
            "license": "항해사",
            "level": "1",
            "round": "1",
        },
    )
    assert response.status_code == 422


def test_get_one_inning_signed_200(signed_client):
    response = signed_client.get(
        "/api/solve/",
        params=solve_params_successful,
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "odapset_id" in response_data
    assert response_data["odapset_id"] is not None


def test_get_one_image_200(client):
    response = client.get(
        "/api/solve/img/항해사/D1_2021_01/D1_2021_01-pic1422.png",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_get_one_image_403(client):
    """
    Emulate a directory traversal attack by sending a malicious path.
    """
    response = client.get(
        "/api/solve/img/..%2f..%2f..%2fforbidden",
    )
    assert response.status_code == 403


def test_get_one_image_404(client):
    """
    Emulate a request for an image path that doesn't exist.
    """
    response = client.get(
        "/api/solve/img/항해사/D2_2021_01/D1_2021_01-pic1422.png",
    )
    assert response.status_code == 404
