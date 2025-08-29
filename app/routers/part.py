from typing import Annotated, Literal
from itertools import groupby
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..dependencies import set_user_in_state
from ..database import get_db
from ..models import User, ExamType, GichulSetType, GichulSetGrade, GichulSetInning
from ..services.solve import retrieve_one_inning


templates = Jinja2Templates(directory="app/templates")


router = APIRouter(prefix="/part", tags=["htmx parts"])


@router.get("/test", response_class=HTMLResponse)
async def get_test_data(request: Request, db: Annotated[Session, Depends(get_db)]):
    users = db.exec(select(User.username, User.indivname)).all()
    return templates.TemplateResponse(
        request, "/partials/user_list.html", {"users": users}
    )


@router.get(
    "/solve", response_class=HTMLResponse, dependencies=[Depends(set_user_in_state)]
)
async def get_solve_questions(
    request: Request,
    year: Literal["2021", "2022", "2023"],
    license: GichulSetType,
    level: GichulSetGrade,
    round: GichulSetInning,
    db: Annotated[Session, Depends(get_db)],
):
    user = getattr(request.state, "user", None)
    one_inning = retrieve_one_inning(
        ExamType.real, year, license, level, round, db, user
    )
    subject_dict = {
        subject: list(questions)
        for subject, questions in groupby(
            one_inning.qnas, key=lambda q: q.subject.value
        )
    }
    return templates.TemplateResponse(
        request,
        "/partials/question_list.html",
        {
            "subject_dict": subject_dict,
            "subject_keys": list(subject_dict.keys()),
            "odapset_id": one_inning.odapset_id,
        },
    )
