from langchain_core.runnables import Runnable
from apscheduler.schedulers.background import BackgroundScheduler
from db import DataBase

scheduler = BackgroundScheduler()


def generate_tweet_from_latest_log(db: DataBase, tweet_llm_chain: Runnable):
    latest_log = db.get_latest_log()
    if not latest_log:
        return

    # delete latest log from db
    if not db.remove_log(latest_log.doc_id):
        print(f"Failed to remove log with id {latest_log.doc_id}")
        return

    try:
        tweet = tweet_llm_chain.invoke(
            {
                "log": latest_log["log"],
                "summarized_logs": "",
            }
        )
        db.add_tweet(tweet)

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
    )
    scheduler.start()


def stop_tweet_scheduler():
    scheduler.shutdown()
