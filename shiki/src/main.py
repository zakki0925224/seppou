from fastapi import FastAPI
from contextlib import asynccontextmanager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from llm import create_llm_interface
from db import DataBase
from routers.debug import create_debug_router
from routers.log import router as log_router
from schedules.tweet import start_tweet_scheduler, stop_tweet_scheduler
import uvicorn
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL")
LOCAL_MODEL = os.getenv("LOCAL_MODEL")
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL")
CUSTOM_INSTS_TWEET = os.getenv("CUSTOM_INSTS_TWEET")
CUSTOM_INSTS_SUMMARIZE_LOG = os.getenv("CUSTOM_INSTS_SUMMARIZE_LOG")

# True: local LLM, False: Gemini
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "False").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    start_tweet_scheduler(app.state.db, tweet_chain)

    yield

    # shutdown
    stop_tweet_scheduler()
    app.state.db.close()


app = FastAPI(
    title="Shiki",
    version="0.1.0",
    description="Generates emotional text using LLMs based on system data, transforming technical states into human-relatable expressions.",
    lifespan=lifespan,
)

llm = create_llm_interface(
    google_api_key=GOOGLE_API_KEY,
    google_model=GOOGLE_MODEL,
    local_base_url=LOCAL_BASE_URL,
    local_model=LOCAL_MODEL,
    use_local_llm=USE_LOCAL_LLM,
)

app.state.db = DataBase(db_path="db.json")

# create retrievers for RAG
log_retriever = app.state.db.get_log_retriever(k=3)
tweet_retriever = app.state.db.get_tweet_retriever(k=3)


def format_docs(docs):
    if not docs:
        return "No similar past data found."
    return "\n\n".join([f"- {doc.page_content}" for doc in docs])


# build RAG chain with retrievers
tweet_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CUSTOM_INSTS_TWEET),
        (
            "user",
            "Current log: {log}\n\nSimilar past logs:\n{past_logs}\n\nSimilar past reactions:\n{past_tweets}",
        ),
    ]
)

tweet_chain = (
    {
        "log": RunnablePassthrough(),
        "past_logs": log_retriever | format_docs,
        "past_tweets": tweet_retriever | format_docs,
    }
    | tweet_prompt
    | llm
    | StrOutputParser()
)

debug_router = create_debug_router(llm)
app.include_router(debug_router)
app.include_router(log_router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
