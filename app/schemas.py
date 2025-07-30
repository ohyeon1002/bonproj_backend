from datetime import datetime
from typing import Any, Optional, List, Literal, Dict, Annotated
from pydantic import BaseModel, BeforeValidator, EmailStr, ConfigDict
from sqlmodel import SQLModel, Field
from .models import (
    GichulQnaBase,
    UserBase,
    ExamChoice,
    ExamType,
    GichulSubject,
    GichulSet,
    GichulSetType,
    GichulSetGrade,
    GichulSetInning,
)


# main.py
class RootResponse(BaseModel):
    message: str
    endpoints: str


# solve
class QnaWithImgPaths(GichulQnaBase):
    imgPaths: Optional[List[str]] = None


class SolveResponse(BaseModel):
    odapset_id: Optional[int] = None
    qnas: List[QnaWithImgPaths]


# cbt
class CBTWithImgPaths(BaseModel):
    qnum: int
    subject: str
    ex1str: str
    ex3str: str
    answer: str
    gichulset_id: int
    id: int
    questionstr: str
    ex2str: str
    ex4str: str
    explanation: Optional[str] = None
    imgPaths: Optional[List[str]] = None


class CBTResponse(BaseModel):
    odapset_id: Optional[int] = None
    subjects: Dict[str, List[CBTWithImgPaths]]


# auth
class CreateUser(UserBase):
    password: str = Field(min_length=8)


class SignMeResponse(BaseModel):
    username: str
    indivname: str
    profile_img_url: Optional[str] = None


class CreateUserResponse(BaseModel):
    email: str
    name: str
    message: str = "User successfully registered!"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# result
def strip_if_str(v: Any) -> Any:  # str 공백 제거
    if isinstance(v, str):
        return v.strip()
    return v


StrippedExamChoice = Annotated[
    ExamChoice, BeforeValidator(strip_if_str)
]  # space가 삽입될 수 있는 Enum 타입에 대해 Enum 유효성 검사 전 str 공백 제거


class UserSolvedQna(BaseModel):
    choice: StrippedExamChoice
    gichulqna_id: int
    answer: StrippedExamChoice
    odapset_id: int


class OneResult(BaseModel):
    choice: Optional[StrippedExamChoice] = None
    answer: StrippedExamChoice
    gichulqna_id: int


class ManyResults(BaseModel):
    odapset_id: int
    duration_sec: Optional[int]
    results: List[OneResult]


class ResultsGot(BaseModel):
    resultset_id: int
    created_date: datetime
    exam_type: ExamType
    resultlist: List[OneResult]


class ModelMaterials(BaseModel):
    wrong: str
    examresults: str


class QnAInfo(BaseModel):
    pass


class GichulQnaResponse(SQLModel):
    id: int
    subject: GichulSubject
    qnum: Optional[int]
    questionstr: Optional[str]
    ex1str: Optional[str]
    ex2str: Optional[str]
    ex3str: Optional[str]
    ex4str: Optional[str]
    answer: Optional[str]
    explanation: Optional[str]
    gichulset_id: Optional[int]


class ResultResponse(SQLModel):
    id: int
    choice: Optional[ExamChoice]
    correct: bool
    gichul_qna: GichulQnaResponse


class ResultSetResponse(SQLModel):
    id: int
    examtype: ExamType
    created_date: Optional[datetime]
    duration_sec: Optional[int]
    total_amount: Optional[int]
    total_score: Optional[int]
    passed: bool
    results: List[ResultResponse]


# mypage
class GichulInfo(SQLModel):
    year: Optional[int]
    type: Optional[GichulSetType]
    grade: Optional[GichulSetGrade]
    inning: Optional[GichulSetInning]


class GichulQnaInResult(SQLModel):
    id: Optional[int]
    subject: GichulSubject
    qnum: Optional[int]
    questionstr: Optional[str]
    ex1str: Optional[str]
    ex2str: Optional[str]
    ex3str: Optional[str]
    ex4str: Optional[str]
    answer: Optional[str]
    explanation: Optional[str]
    gichulset: Optional[GichulInfo]
    gichulset_id: Optional[int]


class ResultWithGichulQnaInResultSet(SQLModel):
    id: Optional[int]
    correct: Optional[bool]
    choice: Optional[ExamChoice]
    hidden: Optional[bool]
    gichul_qna: Optional[GichulQnaInResult] = None


class ResultSetWithResult(SQLModel):
    id: Optional[int]
    examtype: ExamType
    created_date: Optional[datetime]
    results: List[ResultWithGichulQnaInResultSet] = []
