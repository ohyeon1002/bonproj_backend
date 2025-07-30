from typing import Optional
from sqlmodel import Session, select
from ..models import Chat, ChatTurn, User


def create_one_chat(current_user: Optional[User], db: Session):
    new_chat_session = Chat(user=current_user)
    db.add(new_chat_session)
    db.flush()
    db.refresh(new_chat_session)
    return new_chat_session


def create_one_chat_turn(
    chat_id: int,
    prompt: Optional[str],
    db: Session,
    response: Optional[str] = None,
    turn_num: Optional[int] = None,
):
    new_chat_turn = ChatTurn(
        chat_id=chat_id, prompt=prompt, response=response, turn_num=turn_num
    )
    db.add(new_chat_turn)
    return new_chat_turn


def read_chats(current_user: User, db: Session):
    return db.exec(select(Chat).where(Chat.user_id == current_user.id)).all()
