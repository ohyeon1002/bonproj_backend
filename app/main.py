from fastapi import FastAPI
from .routers import auth, result, solve, modelcall, cbt, mypage
from .schemas import RootResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

app.include_router(solve.router)

app.include_router(modelcall.router)

app.include_router(cbt.router)

app.include_router(result.router)

app.include_router(mypage.router)


@app.get("/", response_model=RootResponse)
def read_root():
    return {
        "message": "This is the GET method from the very root end.",
        "endpoints": "You can call /auth, /solve, /modelcall for practical features",
    }
