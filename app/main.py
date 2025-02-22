from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()


# DB 세션 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/db-test")
def read_root(db: Session = Depends(get_db)):
    # DB 연결 테스트 예시
    result = db.execute("SELECT 1").fetchone()
    if not result:
        raise HTTPException(status_code=500, detail="DB 연결 실패")
    return {"message": "Hello, FastAPI!", "db_test": result[0]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
