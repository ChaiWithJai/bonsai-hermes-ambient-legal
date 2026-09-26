"""Hermes cron context: print the local review date at execution time."""
from datetime import datetime
from zoneinfo import ZoneInfo

print("Review date (America/New_York): " + datetime.now(ZoneInfo("America/New_York")).date().isoformat())
