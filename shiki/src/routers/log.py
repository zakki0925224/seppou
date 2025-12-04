from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import json

from db import DataBase

router = APIRouter(prefix="/log", tags=["log"])


class LogRequest(BaseModel):
    content: str


@router.post("/")
async def post_log(request: Request, log_request: LogRequest):
    db: DataBase = request.app.state.db
    content = log_request.content

    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")

    print(f'Received log: "{content}"')
    data = db.add_log(content)

    return {"status": "success", "data": data}
