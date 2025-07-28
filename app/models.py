import enum
from datetime import datetime
from typing import List, Optional, ClassVar
from sqlmodel import (
    SQLModel,
    Field,
    Column,
    Relationship,
    TIMESTAMP,
    Text,
)
from pydantic import EmailStr
from sqlalchemy.sql import func
from sqlalchemy import Column, Enum as SQLAlchemyEnum, Text

# Enum 정의


class GichulSetType(str, enum.Enum):
    gigwansa = "기관사"
    hanghaesa = "항해사"
    sohyeong = "소형선박조종사"


class GichulSetGrade(str, enum.Enum):
    grade_none = "0"
    grade_1 = "1"
    grade_2 = "2"
    grade_3 = "3"
    grade_4 = "4"
    grade_5 = "5"
    grade_6 = "6"


class GichulSetInning(str, enum.Enum):
    inning_1 = "1"
    inning_2 = "2"
    inning_3 = "3"
    inning_4 = "4"


class GichulSubject(str, enum.Enum):
    hanghae = "항해"
    unyong = "운용"
    beopgyu = "법규"
    english = "영어"
    sangseon = "상선전문"
    eoseon = "어선전문"
    gigwan1 = "기관1"
    gigwan2 = "기관2"
    gigwan3 = "기관3"
    gigwan = "기관"
    jikmu = "직무일반"


class ExamType(str, enum.Enum):
    practice = "practice"
    real = "exam"
    cbt = "cbt"


class ExamChoice(str, enum.Enum):
    ex1 = "가"
    ex2 = "나"
    ex3 = "사"
    ex4 = "아"


# SQLModel 정의
class UserBase(SQLModel):
    username: EmailStr = Field(
        max_length=45, unique=True, index=True, description="email address"
    )
    indivname: str = Field(max_length=45, description="full name")


class DBUser(UserBase):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[str] = Field(
        default=None, max_length=60, description="only for traditional sign-in"
    )
    google_sub: Optional[str] = Field(
        default=None, description="unique subject identifier from Google OAuth"
    )
    profile_img_url: Optional[str] = Field(
        default=None, description="typically given from Google account"
    )
    disabled: bool = Field(default=False, description="status of soft-delete")


class User(DBUser, table=True):
    """사용자 정보 테이블"""

    __tablename__: ClassVar[str] = "user"

    chats: List["Chat"] = Relationship(back_populates="user")
    resultsets: List["ResultSet"] = Relationship(back_populates="user")


class GichulSet(SQLModel, table=True):
    """기출문제 세트 정보 테이블"""

    __tablename__: ClassVar[str] = "gichulset"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: GichulSetType = Field(
        sa_column=Column(
            SQLAlchemyEnum(
                GichulSetType, values_callable=lambda x: [e.value for e in x]
            )
        ),
        description="시험 종류 | the certification of purpose",
    )
    grade: GichulSetGrade = Field(
        sa_column=Column(
            SQLAlchemyEnum(
                GichulSetGrade, values_callable=lambda x: [e.value for e in x]
            )
        ),
        description="급수 | grade of the specific exam type",
    )
    year: int
    inning: GichulSetInning = Field(
        sa_column=Column(
            SQLAlchemyEnum(
                GichulSetInning, values_callable=lambda x: [e.value for e in x]
            )
        ),
        description="회차 | inning of the exam in each year",
    )

    qnas: List["GichulQna"] = Relationship(back_populates="gichulset")


class Chat(SQLModel, table=True):
    """채팅 세션 정보 테이블"""

    __tablename__: ClassVar[str] = "chat"

    id: Optional[int] = Field(default=None, primary_key=True)
    create_date: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )

    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

    user: Optional[User] = Relationship(back_populates="chats")
    chat_turns: List["ChatTurn"] = Relationship(back_populates="chat")


class ChatTurn(SQLModel, table=True):
    """개별 대화 턴 (질문-답변) 정보 테이블"""

    __tablename__: ClassVar[str] = "chatturns"

    id: Optional[int] = Field(default=None, primary_key=True)
    turn_num: Optional[int] = Field(default=None)
    prompt: Optional[str] = Field(default=None, sa_column=Column(Text))
    response: Optional[str] = Field(default=None, sa_column=Column(Text))

    chat_id: Optional[int] = Field(default=None, foreign_key="chat.id")
    chat: Optional[Chat] = Relationship(back_populates="chat_turns")


class GichulQnaBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: GichulSubject = Field(
        sa_column=Column(
            SQLAlchemyEnum(
                GichulSubject, values_callable=lambda x: [e.value for e in x]
            )
        )
    )
    qnum: Optional[int] = Field(default=None)
    questionstr: Optional[str] = Field(default=None, sa_column=Column(Text))
    ex1str: Optional[str] = Field(default=None, sa_column=Column(Text))
    ex2str: Optional[str] = Field(default=None, sa_column=Column(Text))
    ex3str: Optional[str] = Field(default=None, sa_column=Column(Text))
    ex4str: Optional[str] = Field(default=None, sa_column=Column(Text))
    answer: Optional[str] = Field(default=None, max_length=45)
    explanation: Optional[str] = Field(
        default=None,
        max_length=450,
        description="explanation from a SOTA or in-house model",
    )
    gichulset_id: Optional[int] = Field(default=None, foreign_key="gichulset.id")


class GichulQna(GichulQnaBase, table=True):
    """개별 기출문제 정보 테이블"""

    __tablename__: ClassVar[str] = "gichulqna"

    gichulset: Optional[GichulSet] = Relationship(back_populates="qnas")
    results: List["Result"] = Relationship(back_populates="gichul_qna")


class ResultSet(SQLModel, table=True):
    """모의 시험 결과 정보"""

    __tablename__: ClassVar[str] = "resultset"

    id: Optional[int] = Field(default=None, primary_key=True)
    examtype: ExamType = Field(
        sa_column=Column(
            SQLAlchemyEnum(ExamType, values_callable=lambda x: [e.value for e in x])
        )
    )
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_date: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    duration_sec: Optional[int] = Field(
        default=None, description="total time taken to complete the exam session"
    )
    total_amount: Optional[int] = Field(
        default=None, description="the number of questions in the exam session"
    )
    total_score: Optional[int] = Field(default=None)
    passed: bool = Field(
        default=False, description="whether the user would have passed the exam"
    )

    user: Optional[User] = Relationship(back_populates="resultsets")
    results: List["Result"] = Relationship(back_populates="resultset")


class Result(SQLModel, table=True):
    """사용자의 문제 풀이 테이블"""

    __tablename__: ClassVar[str] = "result"

    id: Optional[int] = Field(default=None, primary_key=True)
    choice: Optional[ExamChoice] = Field(
        default=None,
        sa_column=Column(
            SQLAlchemyEnum(ExamChoice, values_callable=lambda x: [e.value for e in x]),
            nullable=True,
        ),
        description="user selected option",
    )
    correct: bool = Field(default=False, description="whether the user was correct")
    hidden: bool = Field(
        default=False, description="status of soft-delete of the record"
    )
    gichulqna_id: int = Field(foreign_key="gichulqna.id")
    resultset_id: Optional[int] = Field(default=None, foreign_key="resultset.id")

    gichul_qna: Optional[GichulQna] = Relationship(back_populates="results")
    resultset: Optional[ResultSet] = Relationship(back_populates="results")
