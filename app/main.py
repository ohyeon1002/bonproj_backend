import logging
from logging.config import dictConfig
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, result, solve, modelcall, cbt, mypage, page
from .core.logger import LOGGING_CONFIG

dictConfig(LOGGING_CONFIG)

app = FastAPI()

# app.mount("/static", StaticFiles(directory="app/static"), name="static")
# templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용, 개발용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"""
request: {request.method} {request.url.path} | response: {response.status_code} {duration:.4f}s
"""
    )
    return response


app.include_router(auth.router, prefix="/api")
app.include_router(solve.router, prefix="/api")
app.include_router(modelcall.router, prefix="/api")
app.include_router(cbt.router, prefix="/api")
app.include_router(result.router, prefix="/api")
app.include_router(mypage.router, prefix="/api")
# app.include_router(page.router)


@app.get("/")
def read_root():
    return "hello"
    # return templates.TemplateResponse(request, "index.html")
