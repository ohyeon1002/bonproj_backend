from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from ..dependencies import get_current_active_user
from ..models import User
from ..database import get_db
from ..services.modelcall import geminiChat, diagReq


router = APIRouter(prefix="/modelcall", tags=["Call Local or External Models"])


@router.get("/gemini")
async def modelcall_root(user_prompt: str):
    return StreamingResponse(geminiChat(user_prompt), media_type="text/event-stream")


@router.post("/diag")
async def ai_diagnosis(
    wrong: str,
    examresults: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return StreamingResponse(
        diagReq(wrong, examresults, current_user), media_type="text/event-stream"
    )
