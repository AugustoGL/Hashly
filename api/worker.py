"""
Worker de sellado: reintenta envíos y actualiza pruebas pendientes.

    python worker.py            # loop infinito
    python worker.py --once     # una pasada y sale
"""

import sys
import time

from config import OTS_WORKER_INTERVAL
from database.database import SessionLocal
from ots.service import process_all


def run_once() -> dict:
    db = SessionLocal()

    try:
        return process_all(db)
    finally:
        db.close()


def main() -> None:
    if "--once" in sys.argv:
        print(run_once(), flush=True)
        return

    while True:
        try:
            print(run_once(), flush=True)
        except Exception as error:
            print(f"worker error: {error}", flush=True)

        time.sleep(OTS_WORKER_INTERVAL)


if __name__ == "__main__":
    main()
