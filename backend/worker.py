"""RQ worker: run from repo root with `cd backend && python worker.py`."""

import redis
from rq import Connection, Worker

from config import settings


def main() -> None:
    url = (settings.redis_url or "").strip() or "redis://localhost:6379/0"
    conn = redis.from_url(url)
    with Connection(conn):
        Worker(["sandesh-email"]).work()


if __name__ == "__main__":
    main()
