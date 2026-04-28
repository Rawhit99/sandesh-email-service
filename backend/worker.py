# License: MIT
# See LICENSE.
"""Redis queue worker using ThreadPoolExecutor."""

from sandesh.infrastructure.queue.executor import run_worker_loop


def main() -> None:
    run_worker_loop()


if __name__ == "__main__":
    main()
