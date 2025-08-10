from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_db
from ..models import User


templates = Jinja2Templates(directory="app/templates")


router = APIRouter(prefix="/page", tags=["htmx pages"])


@router.get("/test", response_class=HTMLResponse)
async def get_test_data(request: Request, db: Annotated[Session, Depends(get_db)]):
    users = db.exec(select(User.username, User.indivname)).all()
    return templates.TemplateResponse(
        request, "/partials/user_list.html", {"users": users}
    )
