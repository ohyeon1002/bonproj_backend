from typing import Annotated, Optional
from sqlmodel import Session
from fastapi import APIRouter, Request, Response, Cookie, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from ..database import get_db
from ..schemas import Token
from ..services.user import sign_user_in


templates = Jinja2Templates(directory="app/templates")


router = APIRouter(tags=["actual pages to navigate"])


@router.get("/chat", response_class=HTMLResponse)
async def navigate_chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html")


@router.get("/solve", response_class=HTMLResponse)
async def navigate_solve_page(request: Request):
    return templates.TemplateResponse(request, "solve.html")


@router.get("/cbt", response_class=HTMLResponse)
async def navigate_cbt_page(request: Request):
    return templates.TemplateResponse(request, "cbt.html")


@router.get("/calendar", response_class=HTMLResponse)
async def navigate_calendar_page(request: Request):
    return templates.TemplateResponse(request, "calendar.html")


@router.get("/sign", response_class=HTMLResponse)
async def navigate_sign_page(request: Request):
    return templates.TemplateResponse(request, "sign.html")


@router.post("/token")
async def htmx_sign_for_cookie(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    token: Token = sign_user_in(form_data, db)
    access_token = token.access_token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    response.status_code = 200
    response.headers["HX-Redirect"] = "/"
    return response


@router.post("/out")
async def sign_out(cookie: Annotated[Optional[str], Cookie()]):
    pass
