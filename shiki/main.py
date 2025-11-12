from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langserve import add_routes
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL")
LOCAL_MODEL = os.getenv("LOCAL_MODEL")
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL")
CUSTOM_INSTS_TWEET = os.getenv("CUSTOM_INSTS_TWEET")
CUSTOM_INSTS_SUMMARIZE_LOG = os.getenv("CUSTOM_INSTS_SUMMARIZE_LOG")

# True: local llm, False: Gemini
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "False").lower() == "true"

app = FastAPI(
    title="Shiki",
    version="0.1.0",
    description="Generates emotional text using LLMs based on system data, transforming technical states into human-relatable expressions.",
)

if USE_LOCAL_LLM:
    llm = ChatOpenAI(
        api_key="lm-studio",  # dummy
        base_url=LOCAL_BASE_URL,
        model=LOCAL_MODEL,
    )
    current_model = LOCAL_MODEL
    current_provider = "local"
    print(f"Using Local LLM: {LOCAL_MODEL}")
else:
    llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model=GOOGLE_MODEL)
    current_model = GOOGLE_MODEL
    current_provider = "gemini"
    print(f"Using Gemini: {GOOGLE_MODEL}")


@app.get("/model")
async def get_current_model():
    return {
        "provider": current_provider,
        "model": current_model,
    }


tweet_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CUSTOM_INSTS_TWEET),
        ("user", "cpu_log:{cpu_log}\nsummarized_log:{summarized_log}"),
    ]
)

summarize_prompt = ChatPromptTemplate.from_messages(
    [("system", CUSTOM_INSTS_SUMMARIZE_LOG), ("user", "{log_chunk}")]
)

tweet_chain = tweet_prompt | llm | StrOutputParser()
summarize_chain = summarize_prompt | llm | StrOutputParser()

add_routes(app, tweet_chain, path="/tweet")
add_routes(app, summarize_chain, path="/summarize")
add_routes(app, llm, path="/debug")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
