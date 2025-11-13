from langchain_core.runnables import Runnable
from apscheduler.schedulers.background import BackgroundScheduler
from db import DataBase

scheduler = BackgroundScheduler()


def generate_tweet_from_latest_log(db: DataBase, tweet_llm_chain: Runnable):
    latest_log = db.get_latest_log()
    if not latest_log:
        return

    log_id = latest_log.doc_id

    try:
        tweet = tweet_llm_chain.invoke(latest_log["log"])
        db.add_tweet(tweet, log_ids=[log_id])

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
