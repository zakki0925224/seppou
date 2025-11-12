from fastapi import APIRouter
from langserve import add_routes
from langchain_core.runnables import Runnable


def create_debug_router(llm: Runnable) -> APIRouter:
    router = APIRouter(tags=["debug"])
    add_routes(router, llm, path="/debug")

    return router
