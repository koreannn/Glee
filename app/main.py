from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.auth.auth_router import router as auth_router

app = FastAPI()
app.include_router(auth_router)

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
    secret_key="your-secret-key",  # 반드시 변경할 것!
)


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
