signup_url = "/api/auth/signup"


def test_user_signup_200(client):
    response = client.post(
        signup_url,
        json={
            "username": "user2@example.com",
            "indivname": "string",
            "password": "stringst",
        },
    )
    assert response.status_code == 200


def test_user_signup_409(client):
    """
    Emulate sign-up of a user with an already registered email.
    """
    response = client.post(
        signup_url,
        json={
            "username": "pytest@example.com",  # fail
            "indivname": "duplicate user",
            "password": "stringst",
        },
    )
    assert response.status_code == 409


def test_user_signup_422_emailstr(client):
    """
    Emulate sign-up of a user with an invalid email field input.
    """
    response = client.post(
        signup_url,
        json={
            "username": "username",  # fail
            "indivname": "string",
            "password": "stringst",
        },
    )
    assert response.status_code == 422


def test_user_signup_422_password(client):
    """
    Emulate sign-up of a user with an invalid password input.
    """
    response = client.post(
        signup_url,
        json={
            "username": "user2@example.com",
            "indivname": "string",
            "password": "str",  # fail
        },
    )
    assert response.status_code == 422


signin_url = "/api/auth/token"


def test_user_signin_200(client):
    response = client.post(
        signin_url,
        data={"username": "pytest@example.com", "password": "stringst"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert "access_token" in response_data
    assert "token_type" in response_data
    assert str(response_data["token_type"]).startswith("bearer")


# def test_user_signin_400(client):
#     response = client.post(
#         signin_url,
#         data={"username": "disabled@example.com", "password": "stringst"},
#     )
#     assert response.status_code == 400


def test_user_signin_401_not_registered(client):
    response = client.post(
        signin_url,
        data={"username": "doesnexists@example.com", "password": "eopseoyo"},
    )
    assert response.status_code == 401


# def test_user_signin_401(client):
#     pass
