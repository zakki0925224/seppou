import argparse
import os
import sys
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import toml
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from db import DataBase
from llm import create_llm_interface
from routers.debug import create_debug_router
from routers.log import router as log_router
from routers.tweet import router as tweet_router
from schedules.tweet import start_tweet_scheduler, stop_tweet_scheduler

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("config", help="Path to config file")

args = arg_parser.parse_args()
config = toml.load(args.config)

load_dotenv(dotenv_path=config["shiki"]["dotenv_path"])
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
HOST = config["shiki"]["host"]
PORT = config["shiki"]["port"]
GOOGLE_MODEL = config["shiki"]["google_model"]
LOCAL_MODEL = config["shiki"]["local_model"]
LOCAL_BASE_URL = config["shiki"]["local_base_url"]
CUSTOM_INST_CONFIG_PATH = config["shiki"]["custom_inst_config_path"]

# True: local Model, False: Gemini
USE_LOCAL_MODEL = config["shiki"]["use_local_model"]

DB_PATH = config["shiki"]["db_path"]
CHROMA_PATH = config["shiki"]["chroma_path"]

# load toml file
custom_inst_toml = toml.load(CUSTOM_INST_CONFIG_PATH)
SYSTEM_PROMPT = custom_inst_toml["system_prompt"]

# API key check
if GOOGLE_API_KEY == "":
    print("GOOGLE_API_KEY is not defined in .env")
    sys.exit(0)

# parse host name
parsed = urlparse(HOST)
if parsed.scheme:
    HOSTNAME = parsed.hostname or HOST
else:
    HOSTNAME = HOST

# print configurations
print("Configurations:")
print(f"HOST={HOST}")
print(f"PORT={PORT}")
print("GOOGLE_API_KEY=***************************")
print(f"GOOGLE_MODEL={GOOGLE_MODEL}")
print(f"LOCAL_MODEL={LOCAL_MODEL}")
print(f"LOCAL_BASE_URL={LOCAL_BASE_URL}")
print(f"CUSTOM_INST_CONFIG_PATH={CUSTOM_INST_CONFIG_PATH}")
print(f"USE_LOCAL_MODEL={USE_LOCAL_MODEL}")
print(f"DB_PATH={DB_PATH}")
print(f"CHROMA_PATH={CHROMA_PATH}")
print(f"\nLoaded toml: {custom_inst_toml}")


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = create_llm_interface(
    google_api_key=GOOGLE_API_KEY,
    google_model=GOOGLE_MODEL,
    local_base_url=LOCAL_BASE_URL,
    local_model=LOCAL_MODEL,
    use_local_model=USE_LOCAL_MODEL,
)

app.state.db = DataBase(db_path=DB_PATH, chroma_path=CHROMA_PATH)

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
        ("system", SYSTEM_PROMPT),
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
app.include_router(tweet_router)

if __name__ == "__main__":
    uvicorn.run(app, host=HOSTNAME, port=PORT)
