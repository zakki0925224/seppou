import json
import re
import time

import tiktoken
from apscheduler.schedulers.background import BackgroundScheduler
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.runnables import Runnable

from db import DataBase

scheduler = BackgroundScheduler()
encoding = tiktoken.get_encoding("cl100k_base")

config = TemplateMinerConfig()
config.profiling_depth = 5
config.similarity_threshold = 0.6
config.max_children = 100

template_miner = TemplateMiner(config=config)


class PromptCaptureCallback(BaseCallbackHandler):
    def __init__(self):
        self.prompts = ""

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.prompts = "\n".join(prompts)


callback = PromptCaptureCallback()


def calculate_tokens(text: str) -> int:
    return len(encoding.encode(text))


def compress_logs_with_drain(logs: list) -> str:
    all_messages = []
    for log in logs:
        content = log.get("log", "")
        try:
            log_json = json.loads(content)
            if isinstance(log_json, list):
                all_messages.extend([str(item) for item in log_json])
            elif isinstance(log_json, dict):
                all_messages.append(json.dumps(log_json, sort_keys=True))
            else:
                all_messages.append(str(log_json))
        except json.JSONDecodeError:
            all_messages.append(content)

    template_counts = {}
    template_samples = {}

    for message in all_messages:
        normalized = message
        normalized = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", normalized)
        normalized = re.sub(r"\b\d{2,}\b", "<NUM>", normalized)
        normalized = re.sub(r"\br\d+\b", "<REG>", normalized)
        result = template_miner.add_log_message(normalized)

        if result:
            template = result["template_mined"]
            template_counts[template] = template_counts.get(template, 0) + 1
            if template not in template_samples:
                template_samples[template] = message

    sorted_templates = sorted(template_counts.items(), key=lambda x: x[1], reverse=True)

    total_messages = len(all_messages)
    compressed_logs = [
        f"Summary of {total_messages} execution logs (Grouped by similarity):"
    ]

    for template, count in sorted_templates[:15]:
        percentage = (count / total_messages) * 100
        sample = template_samples.get(template, "N/A")
        line = f"- Repeated {count} times ({percentage:.1f}%): {template}\n  Example: {sample}"
        compressed_logs.append(line)

    if len(sorted_templates) > 15:
        remaining = len(sorted_templates) - 15
        total_remaining = sum(count for _, count in sorted_templates[15:])
        remaining_pct = (total_remaining / total_messages) * 100
        compressed_logs.append(
            f"... and {remaining} other minor patterns ({total_remaining}x, {remaining_pct:.1f}%)"
        )

    return "\n".join(compressed_logs)


def generate_tweet_from_latest_log(
    db: DataBase, tweet_llm_chain: Runnable, model_max_context_length: int
):
    latest_logs = db.get_latest_logs()
    if not latest_logs:
        return

    log_ids = [x.doc_id for x in latest_logs]

    reserved_tokens = 1000
    available_tokens = model_max_context_length - reserved_tokens

    compressed_log = compress_logs_with_drain(latest_logs)
    log_tokens = calculate_tokens(compressed_log)

    print(f"Compressed {len(latest_logs)} logs to {log_tokens} tokens")
    print(f'Compressed log: "{compressed_log}"')

    if log_tokens > available_tokens:
        tokens = encoding.encode(compressed_log)
        truncated_tokens = tokens[:available_tokens]
        compressed_log = encoding.decode(truncated_tokens)
        log_tokens = available_tokens

    log_retriever = db.get_log_retriever(k=3)
    tweet_retriever = db.get_tweet_retriever(k=3)

    past_log_docs = log_retriever.invoke(compressed_log)
    past_tweet_docs = tweet_retriever.invoke(compressed_log)

    remaining_tokens = available_tokens - log_tokens
    past_logs_budget = remaining_tokens // 2
    past_tweets_budget = remaining_tokens - past_logs_budget

    past_logs_content = []
    past_logs_tokens = 0
    for doc in past_log_docs:
        content = f"- {doc.page_content}"
        tokens = calculate_tokens(content)
        if past_logs_tokens + tokens > past_logs_budget:
            break
        past_logs_content.append(content)
        past_logs_tokens += tokens

    past_tweets_content = []
    past_tweets_tokens = 0
    for doc in past_tweet_docs:
        content = f"- {doc.page_content}"
        tokens = calculate_tokens(content)
        if past_tweets_tokens + tokens > past_tweets_budget:
            break
        past_tweets_content.append(content)
        past_tweets_tokens += tokens

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
                "log": compressed_log,
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
