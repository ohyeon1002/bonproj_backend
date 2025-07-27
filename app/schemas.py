from datetime import datetime
from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlmodel import SQLModel, Field
from .models import GichulQnaBase, UserBase, OdapChoice, ExamType, GichulSubject


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


# odap
class UserSolvedQna(BaseModel):
    choice: OdapChoice
    gichulqna_id: int
    odapset_id: int


class OneOdap(BaseModel):
    choice: OdapChoice
    gichulqna_id: int


class ManyOdaps(BaseModel):
    odapset_id: int
    odaps: List[OneOdap]


class OdapsGot(BaseModel):
    odapset_id: int
    created_date: datetime
    exam_type: ExamType
    odaplist: List[OneOdap]


# mypage


class GichulQnaInOdap(SQLModel):
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


class OdapWithGichulQnaInOdapSet(SQLModel):
    id: Optional[int]
    choice: OdapChoice
    gichul_qna: Optional[GichulQnaInOdap] = None


class OdapSetWithOdap(SQLModel):
    id: Optional[int]
    examtype: ExamType
    created_date: Optional[datetime]
    odaps: List[OdapWithGichulQnaInOdapSet] = []
