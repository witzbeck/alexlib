"""Constants for alexlib."""

from datetime import datetime
from pathlib import Path
from string import ascii_letters, digits

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = f"{DATE_FORMAT}T{TIME_FORMAT}"
EPOCH = datetime(1000, 1, 1)
EPOCH_SECONDS = EPOCH.timestamp()

MODULE_PATH = Path(__file__).parent
SOURCE_PATH = MODULE_PATH.parent
PROJECT_PATH = SOURCE_PATH.parent

RESOURCES_PATH = PROJECT_PATH / "resources"
DATA_PATH = PROJECT_PATH / "data"
LOG_PATH = PROJECT_PATH / "logs"
RECIPES_PATH = DATA_PATH / "recipe_files"

PYPROJECT_PATH = PROJECT_PATH / "pyproject.toml"
DOTENV_PATH = PROJECT_PATH / ".env"
HOME = Path.home()
(CREDS := HOME / ".creds").mkdir(exist_ok=True)
(VENVS := HOME / ".venvs").mkdir(exist_ok=True)


ENVIRONMENTS = ("dev", "test", "prod")

SQL_CHARS = f"{ascii_letters} _{digits}"

SQL_INFOSCHEMA_COL = "select * from information_schema.columns"

CLIPBOARD_COMMANDS_PATH = RESOURCES_PATH / "clipboard_commands_map.json"
COLUMN_SUB_PATH = RESOURCES_PATH / "column_substitution_map.json"
SA_DIALECT_MAP_PATH = RESOURCES_PATH / "sqlalchemy_dialect_map.json"
