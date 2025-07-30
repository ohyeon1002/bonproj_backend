from typing import Annotated, Optional
from fastapi import APIRouter, Depends, UploadFile, Form, File
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from ..dependencies import get_current_active_user, get_optional_current_activate_user
from ..models import User
from ..database import get_db
from ..services.modelcall import (
    stream_save_gemini_chat,
    diagReq,
    retrieve_chat_sessions,
)
from ..schemas import ModelMaterials


router = APIRouter(prefix="/modelcall", tags=["Call Local or External Models"])


@router.get("/history")
def get_chat_histories(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return retrieve_chat_sessions(current_user, db)


@router.post("/gemini")
async def modelcall_root(
    user_prompt: Annotated[Optional[str], Form(description="A question to ask to AI")],
    img_file: Annotated[
        Optional[UploadFile], File(description="A picture to get explained")
    ],
    current_user: Annotated[
        Optional[User], Depends(get_optional_current_activate_user)
    ],
    db: Annotated[Session, Depends(get_db)],
):
    img_content: Optional[bytes] = None
    img_mime_type: Optional[str] = None
    if img_file:
        img_content = await img_file.read()
        img_mime_type = img_file.content_type

    model_response = stream_save_gemini_chat(
        current_user, user_prompt, img_content, img_mime_type, db
    )
    return StreamingResponse(model_response, media_type="text/event-stream")


@router.post("/diag")
async def ai_diagnosis(
    body: ModelMaterials,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return StreamingResponse(
        diagReq(body.wrong, body.examresults, current_user),
        media_type="text/event-stream",
    )
