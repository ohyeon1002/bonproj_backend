<a href="./README.en.md">🇺🇸 English</a>
# 부산대학교 KDT 2025년 1회 과정 프로젝트 2팀
## 소개
해기사 시험 대비 LLM 프로젝트의 백엔드 웹 어플리케이션입니다. 우리 프로젝트에서는 해기사 관련 질의응답 LLM, 기출문제 풀이, 모의고사, 오답노트 기능을 제공하며, 각 문제 풀이에 대해 채점과 합부 판정, 문제 해설 또한 제공됩니다. 백엔드는 로컬 LLM 모델 연동 편의를 위해 파이썬 FastAPI 프레임워크로 제작하였습니다. 사용 DB는 MySQL, 테스트용 DB는 SQLite로 파일을 하나 생성하여 쓰도록 되어 있습니다.

## 개발 사항
서비스에 필요한 API Endpoint

기출문제 DB 데이터 입력 스크립트

http 요청에 대한 간단한 로깅

모든 Endpoint의 응답 성공/실패 테스트 코드


## 설치
```cmd
cd <프로젝트 폴더>
python -m venv .venv
.venv/scripts/activate
pip install -r requirements.txt
```
환경변수를 적절히 설정한 다음 /scripts/jsonImport.py를 실행합니다.
```cmd
fastapi run main/app.py --host 0.0.0.0
```


## 파일 구조
| 파일 / 디렉토리 | 설명 |
| :--- | :--- |
| `project_root/` | |
| `├───requirements.txt` | 의존성 패키지 목록 |
| `├───app/` | FastAPI 애플리케이션 메인 폴더 |
| `│   ├───database.py` | 데이터베이스 세션 및 연결 설정 |
| `│   ├───dependencies.py` | 의존성 주입(DI) 관련 함수 |
| `│   ├───main.py` | FastAPI 애플리케이션 시작점
| `│   ├───models.py` | SQLAlchemy ORM 모델 |
| `│   ├───schemas.py` | Pydantic 스키마
| `│   ├───core/` | 환경변수, 보안 설정 등 |
| `│   ├───routers/` | API 엔드포인트(라우터) 정의 |
| `│   ├───services/` | 비즈니스 로직 처리 계층 |
| `│   ├───crud/` | 데이터베이스 CRUD 로직 |
| `│   ├───static/` | CSS, JavaScript, 이미지 등 정적 파일 |
| `│   ├───templates/` | HTML 템플릿 파일 |
| `│   └───utils/` | 재사용 가능한 유틸리티 함수 |
| `├───notebooks/` | 테스트용 Jupyter Notebook |
| `├───scripts/` | DB 초기화, 데이터 삽입 등 일회성 스크립트 |
| `└───tests/` | Pytest를 사용한 테스트 코드 |


## API Endpoint 소개
1. 인증
    - `POST` `/api/auth/signup` : 회원 가입
    - `POST` `/api/auth/token` : 로그인 및 액세스 토큰 발급
    - `GET` `/api/auth/me` : 사용자 정보 조회
    - `GET` `/api/auth/login/google` : 구글 소셜 로그인 요청
    - `GET` `/api/auth/sign/google` : 구글 소셜 로그인 콜백 처리


2. 기출 문제 제공
    - `GET` `/api/solve/` : 특정 회차 문제 세트 조회
    - `GET` `/api/solve/img/{endpath}` : 문제 이미지 제공


3. 모델 호출
    - `GET` `/api/modelcall/history` : 채팅 기록 조회
    - `POST` `/api/modelcall/gemini` : Gemini 모델 호출
    - `POST` `/api/modelcall/diag` : AI 진단 요청


4. 랜덤 CBT 문제
    - `GET` `/api/cbt/` : 랜덤 QnA 세트 조회


5. 사용자 풀이 결과
    - `POST` `/api/results/save` : 단일 문제풀이 저장
    - `POST` `/api/results/savemany` : 다수 문제풀이 저장
    - `DELETE` `/api/results/{result_id}` : 특정 오답노트 삭제
    - `GET` `/api/results/{resultset_id}` : 시험 결과 상세 조회


6. 마이페이지
    - `GET` `/api/mypage/odaps` : 마이페이지 오답 노트 조회
    - `GET` `/api/mypage/cbt_results` : 마이페이지 CBT 결과 조회
    - `GET` `/api/mypage/exam_results` : 마이페이지 시험 결과 조회

## 미구현 / 개선 필요
1. Google 로그인 시 액세스 토큰을 URL 파라미터로 전달하는 방식 개선 필요
2. 이미지가 사용된 문제에 대한 해설 미제작
3. 비동기 처리 미도입
4. 테스트 로직에서 문제 저장을 여러번 반복했을 경우에 대한 테스트 x