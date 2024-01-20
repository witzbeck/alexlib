"""Constants for alexlib."""
from datetime import datetime
from pathlib import Path
from string import ascii_letters, digits


ENVS = ["dev", "test", "prod"]
SQL_CHARS = f"{ascii_letters} _{digits}"
QG_SUBS = {
    " ": "_",
    "-": "_",
    "#": "NUMBER",
    "&": "AND",
    "/": "_",
    "%": "PERCENT",
    ".": "",
}
QG_KEYS = list(QG_SUBS.keys())

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = DATE_FORMAT + " " + TIME_FORMAT
EPOCH = datetime(1000, 1, 1)
EPOCH_SECONDS = EPOCH.timestamp()

HOME = Path.home()
(CREDS := HOME / ".creds").mkdir(exist_ok=True)
(VENVS := HOME / ".venvs").mkdir(exist_ok=True)
