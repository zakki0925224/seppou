from fastapi import APIRouter, Request, HTTPException
from db import DataBase

router = APIRouter(prefix="/tweet", tags=["tweet"])


@router.get("/")
async def get_tweet(request: Request):
    db: DataBase = request.app.state.db
    tweet = db.get_latest_tweet()
    if not tweet:
        raise HTTPException(status_code=404, detail="No tweet found.")

    return {"status": "success", "data": tweet}
