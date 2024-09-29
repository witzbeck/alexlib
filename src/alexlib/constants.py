"""Constants for alexlib."""

from calendar import EPOCH
from datetime import datetime
from pathlib import Path
from string import ascii_letters, digits

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = f"{DATE_FORMAT}T{TIME_FORMAT}"
EPOCH = datetime(EPOCH, 1, 1)
EPOCH_SECONDS = EPOCH.timestamp()

MODULE_PATH = Path(__file__).parent
SOURCE_PATH = MODULE_PATH.parent
PROJECT_PATH = SOURCE_PATH.parent

RESOURCES_PATH = PROJECT_PATH / "resources"
DATA_PATH = PROJECT_PATH / "data"

LOG_PATH = PROJECT_PATH / "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

RECIPES_PATH = DATA_PATH / "recipe_files"

PYPROJECT_PATH = PROJECT_PATH / "pyproject.toml"
DOTENV_PATH = PROJECT_PATH / ".env"
HOME = Path.home()
(CREDS := HOME / ".creds").mkdir(exist_ok=True)
(VENVS := HOME / ".venvs").mkdir(exist_ok=True)


ENVIRONMENTS = ("dev", "test", "prod")

SQL_CHARS = f"{ascii_letters} _{digits}"

SQL_INFOSCHEMA_COL = "select * from information_schema.columns"

CLIPBOARD_COMMANDS_MAP = {
    "windows": ["clip"],
    "macos": ["pbcopy"],
    "linux": [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]],
}
COLUMN_SUB_MAP = {
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
SA_DIALECT_MAP = {
    "postgres": "postgresql+psycopg://",
    "oracle": "oracle+oracledb://",
    "mssql": "mssql+pyodbc://",
    "mysql": "mysql+mysqldb://",
    "sqlite": "sqlite:///",
}
