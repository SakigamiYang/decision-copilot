# coding: utf-8
import os

from redis import Redis
from rq import Queue

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.environ.get("DECISION_COPILOT_QUEUE", "decision-copilot")


def get_redis() -> Redis:
    return Redis.from_url(REDIS_URL)


def get_queue() -> Queue:
    return Queue(name=QUEUE_NAME, connection=get_redis())
