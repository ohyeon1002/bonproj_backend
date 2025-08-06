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


def test_user_signin_401_not_registered(client):
    """
    Emulate sign-in attempt from a user who isn't registered.
    """
    response = client.post(
        signin_url,
        data={"username": "doesnexists@example.com", "password": "eopseoyo"},  # fail
    )
    assert response.status_code == 401


signme_url = "/api/auth/sign/me"


def test_user_sign_me_200(client):
    """
    Emulate sending a jwt to get user info.
    """
    token_response = client.post(
        signin_url,
        data={"username": "pytest@example.com", "password": "stringst"},
    )
    token_response_data = token_response.json()
    access_token = token_response_data["access_token"]

    response = client.get(
        signme_url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "username" in response_data
    assert "indivname" in response_data
    assert "profile_img_url" in response_data
    assert response_data["username"] == "pytest@example.com"
    assert response_data["indivname"] == "Ben Davis"
    assert response_data["profile_img_url"] is None


def test_user_sign_me_400(client):
    """
    Emulate sending a jwt of a disabled user.
    """
    token_response = client.post(
        signin_url,
        data={"username": "disabled@example.com", "password": "stringst"},  # fail
    )
    token_response_data = token_response.json()
    access_token = token_response_data["access_token"]

    response = client.get(
        signme_url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400


def test_user_sign_me_401(client):
    """
    Emulate sending an invalid jwt token.
    """
    from datetime import timedelta
    from app.utils.user_utils import create_access_token

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        {"sub": "fake user"}, access_token_expires
    )  # fail
    response = client.get(
        signme_url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401


# TODO: mock Google signing
