from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from datetime import datetime
from typing import Dict, Optional, List
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from pydantic import Field
import chromadb


class LogRetriever(BaseRetriever):
    """LangChain Retriever for log vector search"""

    collection: chromadb.Collection = Field(default=None, exclude=True)
    k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        results = self.collection.query(query_texts=[query], n_results=self.k)

        documents = []
        if results["ids"] and results["ids"][0]:
            for idx, doc_id in enumerate(results["ids"][0]):
                documents.append(
                    Document(
                        page_content=results["documents"][0][idx],
                        metadata={
                            "doc_id": doc_id,
                            "timestamp": results["metadatas"][0][idx].get("timestamp"),
                            "distance": (
                                results["distances"][0][idx]
                                if "distances" in results
                                else None
                            ),
                        },
                    )
                )

        return documents


class TweetRetriever(BaseRetriever):
    """LangChain Retriever for tweet vector search"""

    collection: chromadb.Collection = Field(default=None, exclude=True)
    k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        results = self.collection.query(query_texts=[query], n_results=self.k)

        documents = []
        if results["ids"] and results["ids"][0]:
            for idx, doc_id in enumerate(results["ids"][0]):
                documents.append(
                    Document(
                        page_content=results["documents"][0][idx],
                        metadata={
                            "doc_id": doc_id,
                            "timestamp": results["metadatas"][0][idx].get("timestamp"),
                            "distance": (
                                results["distances"][0][idx]
                                if "distances" in results
                                else None
                            ),
                        },
                    )
                )

        return documents


class DataBase:
    def __init__(self, db_path: Optional[str] = None, chroma_path: str = "./chroma_db"):
        if db_path is not None:
            self.db = TinyDB(db_path)
        else:
            self.db = TinyDB(storage=MemoryStorage)

        self.logs = self.db.table("logs")
        self.tweets = self.db.table("tweets")

        self.latest_seen_log_id = 0
        self.latest_seen_tweet_id = 0

        # ChromaDB for vector search
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.log_collection = self.chroma_client.get_or_create_collection(
            name="logs", metadata={"hnsw:space": "cosine"}
        )
        self.tweet_collection = self.chroma_client.get_or_create_collection(
            name="tweets", metadata={"hnsw:space": "cosine"}
        )

    def close(self):
        self.db.close()

    # retriever factories for LangChain integration
    def get_log_retriever(self, k: int = 5) -> LogRetriever:
        """Get a LangChain Retriever for log vector search"""
        return LogRetriever(collection=self.log_collection, k=k)

    def get_tweet_retriever(self, k: int = 5) -> TweetRetriever:
        """Get a LangChain Retriever for tweet vector search"""
        return TweetRetriever(collection=self.tweet_collection, k=k)

    # logs DB with vector store
    def add_log(self, log: str) -> Dict:
        data = {
            "log": log,
            "timestamp": datetime.now().isoformat(),
        }
        doc_id = self.logs.insert(data)

        # add to ChromaDB for semantic search
        self.log_collection.add(
            documents=[log],
            ids=[str(doc_id)],
            metadatas=[{"timestamp": data["timestamp"]}],
        )

        return data

    def get_latest_logs(self) -> List[Dict]:
        all_logs = self.logs.all()
        new_logs = [log for log in all_logs if log.doc_id > self.latest_seen_log_id]

        if not new_logs:
            return []

        new_logs.sort(key=lambda x: x.doc_id)
        self.latest_seen_log_id = new_logs[-1].doc_id
        return new_logs

    def remove_log(self, doc_id: int) -> bool:
        result = self.logs.remove(doc_ids=[doc_id])
        # also remove from ChromaDB
        try:
            self.log_collection.delete(ids=[str(doc_id)])
        except Exception:
            pass
        return len(result) > 0

    # tweets DB with vector store
    def add_tweet(
        self,
        tweet: str,
        prompts: str,
        generate_ms: int,
        log_ids: Optional[list[int]] = None,
    ) -> Dict:
        data = {
            "tweet": tweet,
            "prompts": prompts,
            "generate_ms": generate_ms,
            "timestamp": datetime.now().isoformat(),
            "log_ids": log_ids or [],
        }
        doc_id = self.tweets.insert(data)

        # add to ChromaDB
        self.tweet_collection.add(
            documents=[tweet],
            ids=[str(doc_id)],
            metadatas=[{"timestamp": data["timestamp"], "log_ids": str(log_ids or [])}],
        )

        return data

    def get_latest_tweet(self) -> Optional[Dict]:
        all_tweets = self.tweets.all()
        new_tweets = [
            log for log in all_tweets if log.doc_id > self.latest_seen_tweet_id
        ]

        if not new_tweets:
            return None

        new_tweets.sort(key=lambda x: x.doc_id)
        latest_tweet = new_tweets[0]
        self.latest_seen_tweet_id = latest_tweet.doc_id
        return latest_tweet

    def remove_tweet(self, doc_id: int) -> bool:
        result = self.tweets.remove(doc_ids=[doc_id])
        # also remove from ChromaDB
        try:
            self.tweet_collection.delete(ids=[str(doc_id)])
        except Exception:
            pass
        return len(result) > 0
