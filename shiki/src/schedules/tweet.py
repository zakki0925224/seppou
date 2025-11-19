from langchain_core.runnables import Runnable
from langchain_core.callbacks.base import BaseCallbackHandler
from apscheduler.schedulers.background import BackgroundScheduler
from db import DataBase
import time

scheduler = BackgroundScheduler()


class PromptCaptureCallback(BaseCallbackHandler):
    def __init__(self):
        self.prompts = ""

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.prompts = "\n".join(prompts)


callback = PromptCaptureCallback()


def generate_tweet_from_latest_log(db: DataBase, tweet_llm_chain: Runnable):
    latest_logs = db.get_latest_logs()
    if not latest_logs:
        return

    log_ids = [x.doc_id for x in latest_logs]

    formatted_logs = []
    for log in latest_logs:
        formatted_logs.append(log.get("log", ""))

    try:
        start = time.perf_counter_ns()
        tweet = tweet_llm_chain.invoke(
            "\n".join(formatted_logs), config={"callbacks": [callback]}
        )
        end = time.perf_counter_ns()
        generate_ms = int((end - start) / 1000000)
        db.add_tweet(tweet, callback.prompts, generate_ms, log_ids)

    except Exception as e:
        print(f"Error generating tweet: {e}")


def start_tweet_scheduler(
    db: DataBase, tweet_llm_chain: Runnable, interval_seconds: int = 60
):
    scheduler.add_job(
        generate_tweet_from_latest_log,
        "interval",
        seconds=interval_seconds,
        args=[db, tweet_llm_chain],
        max_instances=1,  # do not overlap
        coalesce=True,
    )
    scheduler.start()


def stop_tweet_scheduler():
    scheduler.shutdown()
