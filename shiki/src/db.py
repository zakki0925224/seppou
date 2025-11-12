from tinydb import TinyDB
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

    def close(self):
        self.db.close()

    def get_new_log_id(self) -> int:
        all_logs = self.logs.all()
        if not all_logs:
            return 0

        return max(log["id"] for log in all_logs) + 1

    def add_log(self, log: str) -> Dict:
        next_id = self.get_new_log_id()
        data = {
            "id": next_id,
            "log": log,
            "timestamp": datetime.now().isoformat(),
        }
        self.logs.insert(data)
        return data
