from os import environ
from pathlib import Path
from sys import path

lib = Path(__file__).parent
proj = lib.parent
dotenv = proj / ".env"

path.append(str(lib))
environ.update(
    {
        k: v.strip("'").strip('"')
        for k, v in [
            x.split("=")
            for x in [
                x for x in dotenv.read_text().split("\n") if x and not x.startswith("#")
            ]
        ]
    }
)
