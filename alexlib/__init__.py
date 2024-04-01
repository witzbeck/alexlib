from os import environ
from pathlib import Path
from sys import path

MODULE_PATH = Path(__file__).parent
dotenv = MODULE_PATH.parent / ".env"

path.append(str(MODULE_PATH))
if dotenv.exists():
    environ.update(
        {
            k: v.strip("'").strip('"')
            for k, v in [
                x.split("=")
                for x in [
                    x
                    for x in dotenv.read_text().split("\n")
                    if x and not x.startswith("#")
                ]
            ]
        }
    )
