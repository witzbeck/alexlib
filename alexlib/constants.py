"""Constants for alexlib."""
from datetime import datetime
from pathlib import Path
from string import ascii_letters, digits


CLIPBOARD_CMDS = {
    "windows": ["clip"],
    "macos": ["pbcopy"],
    "linux": [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]],
}

ENVIRONMENTS = ["dev", "test", "prod"]

SQL_CHARS = f"{ascii_letters} _{digits}"
COL_SUBS = {
    " ": "_",
    "-": "_",
    "#": "number",
    "&": "and",
    "/": "_",
    "%": "percent",
    ".": "",
    ",": "",
    "<": "lt",
    ">": "gt",
    "=": "eq",
}
ISTYPE_EXTS = [
    "csv",
    "json",
    "parquet",
    "pickle",
    "xlsx",
    "xls",
    "txt",
    "sql",
    "py",
    "yaml",
    "yml",
    "toml",
    "ini",
    "cfg",
    "conf",
    "env",
    "ipynb",
    "md",
    "rst",
    "html",
]
SQL_SUBS = {k: v for k, v in COL_SUBS.items() if k in SQL_CHARS and k != " "}
SQL_INFOSCHEMA_COL = "select * from information_schema.columns"

SQL_KEYS = list(SQL_SUBS.keys())

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
EPOCH = datetime(1000, 1, 1)
EPOCH_SECONDS = EPOCH.timestamp()

MODULE_PATH = Path(__file__).parent
PROJECT_PATH = MODULE_PATH.parent
HOME = Path.home()
(CREDS := HOME / ".creds").mkdir(exist_ok=True)
(VENVS := HOME / ".venvs").mkdir(exist_ok=True)
