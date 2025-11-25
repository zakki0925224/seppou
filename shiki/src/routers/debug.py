from fastapi import APIRouter
from langchain_core.runnables import Runnable
from langserve import add_routes


def create_debug_router(llm: Runnable) -> APIRouter:
    router = APIRouter(tags=["debug"])
    add_routes(router, llm, path="/debug")

    return router
