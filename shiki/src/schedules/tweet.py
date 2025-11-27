import time

import tiktoken
from apscheduler.schedulers.background import BackgroundScheduler
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.runnables import Runnable

from db import DataBase

scheduler = BackgroundScheduler()
encoding = tiktoken.get_encoding("cl100k_base")


class PromptCaptureCallback(BaseCallbackHandler):
    def __init__(self):
        self.prompts = ""

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.prompts = "\n".join(prompts)


callback = PromptCaptureCallback()


def calculate_tokens(text: str) -> int:
    """Calculate the number of tokens in a text."""
    return len(encoding.encode(text))


def generate_tweet_from_latest_log(
    db: DataBase, tweet_llm_chain: Runnable, model_max_context_length: int
):
    latest_logs = db.get_latest_logs()
    if not latest_logs:
        return

    log_ids = [x.doc_id for x in latest_logs]

    reserved_tokens = 1000
    available_tokens = model_max_context_length - reserved_tokens

    # Build the current log content
    formatted_logs = []
    log_tokens = 0

    for log in reversed(latest_logs):
        content = log.get("log", "")
        tokens = calculate_tokens(content)

        if log_tokens + tokens > available_tokens:
            break

        formatted_logs.append(content)
        log_tokens += tokens

    formatted_logs.reverse()
    current_log = "\n".join(formatted_logs)

    # Get RAG data with token-aware trimming
    log_retriever = db.get_log_retriever(k=10)  # Get more candidates
    tweet_retriever = db.get_tweet_retriever(k=10)  # Get more candidates

    past_log_docs = log_retriever.invoke(current_log)
    past_tweet_docs = tweet_retriever.invoke(current_log)

    # Calculate remaining tokens after current log
    remaining_tokens = available_tokens - log_tokens

    # Allocate tokens: 50% for past logs, 50% for past tweets
    past_logs_budget = remaining_tokens // 2
    past_tweets_budget = remaining_tokens - past_logs_budget

    # Trim past logs to fit budget
    past_logs_content = []
    past_logs_tokens = 0
    for doc in past_log_docs:
        content = f"- {doc.page_content}"
        tokens = calculate_tokens(content)
        if past_logs_tokens + tokens > past_logs_budget:
            break
        past_logs_content.append(content)
        past_logs_tokens += tokens

    # Trim past tweets to fit budget
    past_tweets_content = []
    past_tweets_tokens = 0
    for doc in past_tweet_docs:
        content = f"- {doc.page_content}"
        tokens = calculate_tokens(content)
        if past_tweets_tokens + tokens > past_tweets_budget:
            break
        past_tweets_content.append(content)
        past_tweets_tokens += tokens

    # Format the final past data
    past_logs_text = (
        "\n".join(past_logs_content)
        if past_logs_content
        else "No similar past data found."
    )
    past_tweets_text = (
        "\n".join(past_tweets_content)
        if past_tweets_content
        else "No similar past data found."
    )

    total_tokens = log_tokens + past_logs_tokens + past_tweets_tokens
    print(
        f"Token usage: log={log_tokens}, past_logs={past_logs_tokens}, "
        f"past_tweets={past_tweets_tokens}, total={total_tokens}/{available_tokens}"
    )

    try:
        start = time.perf_counter_ns()
        tweet = tweet_llm_chain.invoke(
            {
                "log": current_log,
                "past_logs": past_logs_text,
                "past_tweets": past_tweets_text,
            },
            config={"callbacks": [callback]},
        )
        end = time.perf_counter_ns()
        generate_ms = int((end - start) / 1000000)
        print(f'Tweet generated in {generate_ms}ms: "{tweet}"')
        db.add_tweet(tweet, callback.prompts, generate_ms, log_ids)

    except Exception as e:
        print(f"Error generating tweet: {e}")


def start_tweet_scheduler(
    db: DataBase,
    tweet_llm_chain: Runnable,
    interval_seconds: int,
    model_max_context_length: int,
):
    scheduler.add_job(
        generate_tweet_from_latest_log,
        "interval",
        seconds=interval_seconds,
        args=[db, tweet_llm_chain, model_max_context_length],
        max_instances=1,  # do not overlap
        coalesce=True,
    )
    scheduler.start()


def stop_tweet_scheduler():
    scheduler.shutdown()
