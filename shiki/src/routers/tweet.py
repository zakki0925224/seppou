from fastapi import APIRouter, Request
from db import DataBase

router = APIRouter(prefix="/tweet", tags=["tweet"])


@router.get("/")
async def get_tweets(request: Request):
    db: DataBase = request.app.state.db
    tweets = db.get_all_tweets()
    return {"status": "success", "data": tweets}
