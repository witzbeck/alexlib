"""Constants for alexlib."""
from datetime import datetime
from pathlib import Path

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = DATE_FORMAT + " " + TIME_FORMAT
epoch = datetime(1000, 1, 1)
epoch_seconds = epoch.timestamp()

home = Path.home()
(creds := home / ".creds").mkdir(exist_ok=True)
(venvs := home / ".venvs").mkdir(exist_ok=True)
