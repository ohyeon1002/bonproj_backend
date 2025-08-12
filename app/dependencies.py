import jwt
from typing import Annotated, Optional
from sqlmodel import Session
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from .database import get_db
from .models import User, UserBase
from .schemas import TokenData
from .core.security import SECRET_KEY, ALGORITHM
from .crud.user_crud import read_one_user


oauth2_scheme_strict = OAuth2PasswordBearer(tokenUrl="api/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="api/auth/token", auto_error=False
)


async def get_token(request: Request) -> Optional[str]:
    header_token = request.headers.get("Authorization")
    if header_token and header_token.startswith("Bearer "):
        return header_token.removeprefix("Bearer ")
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    return None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme_strict)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = read_one_user(token_data.username, db)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_optional_current_user(
    token: Annotated[Optional[str], Depends(get_token)],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    try:
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except InvalidTokenError:
        return None
    user = read_one_user(token_data.username, db)
    return user


async def get_optional_current_activate_user(
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)],
):
    if current_user is None:
        return None
    elif current_user.disabled:
        return None
    return current_user
