# coding: utf-8
from dotenv import load_dotenv
from redis import Redis
from rq.worker import SimpleWorker

from decision_copilot.queue.connection import REDIS_URL, QUEUE_NAME

load_dotenv()


def main() -> None:
    redis = Redis.from_url(REDIS_URL)
    worker = SimpleWorker(queues=[QUEUE_NAME], connection=redis)
    worker.work()


if __name__ == "__main__":
    main()
