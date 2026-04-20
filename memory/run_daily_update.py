"""
Daily memory update scheduler
Runs the memory pipeline on a schedule (separate from main UI)
Can be run manually or as a background scheduler
"""

import time
import sys
import os
from datetime import datetime
from threading import Thread

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False


class MemoryScheduler:
    """Scheduler for running memory updates"""

    def __init__(self, interval_hours: int = 24):
        self.interval_hours = interval_hours
        self.scheduler = None
        self.is_running = False

        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _run_update(self):
        """Execute the memory update"""
        from memory.memory_pipeline import MemoryPipeline

        print(f"[{datetime.now().isoformat()}] Running scheduled memory update...")
        try:
            pipeline = MemoryPipeline()
            result = pipeline.run_daily_update()
            print(f"[{datetime.now().isoformat()}] Update complete: {result}")
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Update failed: {e}")

    def start_blocking(self):
        """Start scheduler in blocking mode (for command line)"""
        print(f"Starting memory scheduler (interval: {self.interval_hours} hours)")

        if HAS_APSCHEDULER:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(
                self._run_update,
                IntervalTrigger(hours=self.interval_hours),
                id='memory_update',
                name='Daily Memory Update',
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True

            print("Scheduler started. Press Ctrl+C to stop.")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
        else:
            print("APScheduler not available. Using simple loop.")
            self._run_update()

            while True:
                time.sleep(self.interval_hours * 3600)
                self._run_update()

    def start_background(self):
        """Start scheduler in background thread"""
        thread = Thread(target=self.start_blocking, daemon=True)
        thread.start()
        self.is_running = True
        print("Memory scheduler started in background")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
        self.is_running = False
        print("Memory scheduler stopped")

    def run_once(self):
        """Run update once manually"""
        self._run_update()


def main():
    """CLI entry point for memory scheduler"""
    import argparse

    parser = argparse.ArgumentParser(description='Sweekar Memory Update Scheduler')
    parser.add_argument(
        '--interval',
        type=int,
        default=24,
        help='Update interval in hours (default: 24)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run update once and exit'
    )

    args = parser.parse_args()

    scheduler = MemoryScheduler(interval_hours=args.interval)

    if args.once:
        scheduler.run_once()
    else:
        scheduler.start_blocking()


if __name__ == "__main__":
    main()
