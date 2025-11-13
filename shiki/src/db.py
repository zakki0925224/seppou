from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from datetime import datetime
from typing import Dict, Optional


class DataBase:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is not None:
            self.db = TinyDB(db_path)
        else:
            self.db = TinyDB(storage=MemoryStorage)

        self.logs = self.db.table("logs")
        self.tweets = self.db.table("tweets")

        # add sample log
        self.add_log("pc=0x1234, r0=0x0000, r1=0x1234, r2=0x5678, r3=0x9abc")

    def close(self):
        self.db.close()

    # logs DB
    def add_log(self, log: str) -> Dict:
        data = {
            "log": log,
            "timestamp": datetime.now().isoformat(),
        }
        self.logs.insert(data)
        return data

    def get_latest_log(self) -> Optional[Dict]:
        all_logs = self.logs.all()
        if not all_logs:
            return None

        latest_log = max(all_logs, key=lambda log: log["timestamp"])
        return latest_log

    def remove_log(self, doc_id: int) -> bool:
        result = self.logs.remove(doc_ids=[doc_id])
        return len(result) > 0

    # tweets DB
    def add_tweet(self, tweet: str) -> Dict:
        data = {
            "tweet": tweet,
            "timestamp": datetime.now().isoformat(),
        }
        self.tweets.insert(data)
        return data

    def get_latest_tweet(self) -> Optional[Dict]:
        all_tweets = self.tweets.all()
        if not all_tweets:
            return None

        latest_tweet = max(all_tweets, key=lambda tweet: tweet["timestamp"])
        return latest_tweet

    def remove_tweet(self, doc_id: int) -> bool:
        result = self.tweets.remove(doc_ids=[doc_id])
        return len(result) > 0
