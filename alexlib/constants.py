from datetime import datetime
from pathlib import Path

date_format = "%Y-%m-%d"
time_format = "%H:%M:%S"
datetime_format = date_format + " " + time_format
epoch = datetime(1000, 1, 1)
epoch_seconds = epoch.timestamp()

home = Path.home()
creds = home / ".creds"
venvs = home / ".venvs"
[path.mkdir(exist_ok=True) for path in [creds, venvs]]
