import logging

from loguru import logger

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.requests import Request

from app.auth.auth_router import router as auth_router
from app.suggester.suggester_router import router as analyze_router
from app.core.settings import settings

# ✅ 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()


app.include_router(auth_router)
app.include_router(analyze_router)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# SessionMiddleware 추가하기
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,  # 반드시 변경할 것!

)


# ✅ 미들웨어를 이용한 로깅 추가
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """모든 요청의 정보를 로깅하는 미들웨어"""
        body = await request.body()
        try:
            body_str = body.decode("utf-8") if body else None
        except UnicodeDecodeError:
            body_str = "<binary data>"

        logger.info(f"""
        📌 요청 정보:
        - URL: {request.url}
        - METHOD: {request.method}
        - HEADERS: {dict(request.headers)}
        - QUERY PARAMS: {dict(request.query_params)}
        - BODY: {body_str}
        """)

        response = await call_next(request)
        return response

# ✅ 미들웨어 등록
app.add_middleware(RequestLoggingMiddleware)


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
