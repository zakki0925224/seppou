from fastapi import APIRouter, Request
from pydantic import BaseModel

from db import DataBase

router = APIRouter(prefix="/log", tags=["log"])


class LogRequest(BaseModel):
    content: str


@router.post("/")
async def post_log(request: Request, log_request: LogRequest):
    db: DataBase = request.app.state.db
    content = log_request.content
    print(f'Received log: "{content}"')
    data = db.add_log(content)

    return {"status": "success", "data": data}
