"""
This module provides a comprehensive framework for executing local Extract-Transform-Load (ETL) processes, specifically tailored for handling SQL queries and managing data transformations. It primarily focuses on data extraction from SQL databases, data transformation using Pandas DataFrames, and loading the transformed data into local SQLite databases or CSV files.

Features:
- `LocalETL`: A dataclass representing the local ETL process with functionalities to manage SQL queries, extract data from remote databases, and load into local SQLite or CSV formats.
- `execute_query`: A function that executes a given SQL query, retrieves data in the form of a DataFrame, and stores the result in a queue for asynchronous processing.
- `get_dfs_threaded`: A function to concurrently extract DataFrames from multiple SQL files using multithreading.
- `get_data_dict_series`: A utility to fetch DataFrames from files and return them in a dictionary format.
- `insert_table` and `insert_data`: Functions for inserting DataFrame content into a SQLite database.
- `to_csv`: A static method for exporting DataFrames to CSV files.

The module leverages Python's standard libraries such as `dataclasses`, `threading`, and `queue`, along with external libraries like `pandas` for DataFrame manipulation and `sqlalchemy` for database engine integration. It is part of the 'alexlib' package, showcasing integration with custom modules for enhanced file and directory handling.

Usage:
This module is designed for data engineers and scientists needing to perform ETL operations locally. It simplifies handling large datasets and complex SQL queries, making it an ideal tool for data processing and analysis tasks.

Example:
To use this module, create an instance of `LocalETL` with the required database connections and file paths, and then call the relevant methods to perform ETL tasks such as extracting data, transforming it, and loading it into a desired format (SQLite/CSV).
"""

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from queue import Queue
from sqlite3 import Connection as SqliteConnection
from sqlite3 import Cursor
from sqlite3 import connect as sqlite_connect
from threading import Thread
from typing import Any

from pandas import DataFrame
from sqlalchemy import Engine

from alexlib.core import chkenv
from alexlib.files import Directory, File


def execute_query(
    name: str,
    file: File,
    engine: Engine,
    result_queue: Queue = None,
    replace: tuple[str, str] = None,
) -> None:
    """executes query and puts result in queue"""
    print(f"getting {name}")
    df = file.get_df(eng=engine, replace=replace)
    res = {name: df}
    result_queue.put(res)
    print(f"got {name}")
    return result_queue


def get_dfs_threaded(
    files: dict[str:File],
    engine: Engine | SqliteConnection,
    replace: tuple[str, str] = None,
) -> dict[str:DataFrame]:
    """gets dataframes from files"""
    if isinstance(engine, Engine):
        result_queue = Queue()
        threads = [
            Thread(
                target=execute_query,
                args=[name, file, engine],
                kwargs={"result_queue": result_queue, "replace": replace},
            )
            for name, file in files.items()
        ]
        _ = [thread.start() for thread in threads]
        results = {}
        while not result_queue.empty() or len(results) < len(files):
            results.update(result_queue.get())
        ret = results
    else:
        ret = {
            name: file.get_df(eng=engine, replace=replace)
            for name, file in files.items()
        }
    return ret


def get_data_dict_series(
    files: dict[str:File],
    engine: Engine | SqliteConnection,
    replace: tuple[str, str] = None,
) -> dict[str:DataFrame]:
    """gets dataframes from files"""
    return {
        name: file.get_df(
            eng=engine,
            replace=replace,
        )
        for name, file in files.items()
    }


@dataclass
class LocalETL:
    """executes etl stages locally"""

    remote_engine: Engine = field()
    resources_dir: Directory = field()
    landing_prefix: str = field(default="landing", repr=False)
    main_prefix: str = field(default="main", repr=False)
    localdb_name: str = field(default=":memory:")
    replace: tuple[str, str] = field(default=None, repr=False)

    @cached_property
    def localdb(self) -> SqliteConnection:
        """returns sqlite connection"""
        return sqlite_connect(self.localdb_name)

    @property
    def cursor(self) -> Cursor:
        """returns sqlite cursor"""
        return self.localdb.cursor()

    def get_local_table(self, name: str) -> list[Any]:
        """gets table from local database"""
        return self.cursor.execute("select * from ?;", (name,)).fetchall()

    @cached_property
    def sql_files(self) -> list[File]:
        """returns list of sql files in resources directory"""
        return [x for x in self.resources_dir.filelist if x.name.endswith(".sql")]

    @property
    def file_prefixes(self) -> list[str]:
        """returns list of prefixes for sql files"""
        return list(set(x.path.stem.split("_")[0] for x in self.sql_files))

    @cached_property
    def landing_files(self) -> dict[str:File]:
        """returns dict of landing files"""
        return {
            "_".join(x.path.stem.split("_")[1:]): x
            for x in self.sql_files
            if x.name.startswith(self.landing_prefix)
        }

    @cached_property
    def main_files(self) -> dict[str:File]:
        """returns dict of main files"""
        return {
            "_".join(x.path.stem.split("_")[1:]): x
            for x in self.sql_files
            if x.name.startswith(self.main_prefix)
        }

    @cached_property
    def file_dict(self) -> dict[str : dict[str:File]]:
        """returns dict of file dicts"""
        return {
            prefix: {
                "_".join(x.path.stem.split("_")[1:]): x
                for x in self.sql_files
                if x.name.startswith(prefix)
            }
            for prefix in self.file_prefixes
        }

    @cached_property
    def table_dict(self) -> dict[str:File]:
        """returns dict of tables"""
        return {k: list(v) for k, v in self.file_dict.items()}

    @cached_property
    def landing_tables(self) -> list[str]:
        """returns list of landing tables"""
        return list(self.landing_files.keys())

    @cached_property
    def main_tables(self) -> list[str]:
        """returns list of main tables"""
        return list(self.main_files.keys())

    @staticmethod
    def get_data_dict(
        files: dict[str:File],
        engine: Engine | SqliteConnection,
        replace: tuple[str, str] = None,
    ) -> dict[str:DataFrame]:
        """gets dataframes from files"""
        return get_dfs_threaded(files, engine, replace=replace)

    @cached_property
    def landing_data(self) -> dict[str:DataFrame]:
        """returns dict of landing data"""
        return get_dfs_threaded(
            self.landing_files, self.remote_engine, replace=self.replace
        )

    def get_main_data(self) -> dict[str:DataFrame]:
        """returns dict of main data"""
        return get_dfs_threaded(
            self.main_files,
            self.localdb,
            replace=self.replace,
        )

    @property
    def main_data(self) -> dict[str:DataFrame]:
        """returns dict of main data"""
        return self.get_main_data()

    @staticmethod
    def get_df_dict_lens(data_dict: dict[DataFrame]) -> dict[str:int]:
        """gets dict of dataframe lengths"""
        return {k: len(v) for k, v in data_dict.items()}

    @cached_property
    def landing_lens(self) -> dict[str:int]:
        """returns dict of landing dataframe lengths"""
        return LocalETL.get_df_dict_lens(self.landing_data)

    @property
    def main_lens(self) -> dict[str:int]:
        """returns dict of main dataframe lengths"""
        return LocalETL.get_df_dict_lens(self.main_data)

    @staticmethod
    def insert_table(
        name: str,
        df: DataFrame,
        cnxn: SqliteConnection,
        index: bool = False,
        if_exists: str = "replace",
    ) -> None:
        """inserts dataframe into database"""
        df.to_sql(name, cnxn, index=index, if_exists=if_exists)

    # pylint: disable=expression-not-assigned
    @staticmethod
    def insert_data(
        data_dict: dict[str:DataFrame],
        cnxn: SqliteConnection,
        index: bool = False,
        if_exists: str = "replace",
    ) -> None:
        """inserts data into database"""
        [
            LocalETL.insert_table(
                name, data, cnxn=cnxn, index=index, if_exists=if_exists
            )
            for name, data in data_dict.items()
        ]

    def insert_landing_data(self, **kwargs) -> None:
        """inserts landing data into database"""
        try:
            LocalETL.insert_data(
                self.landing_data,
                self.localdb,
                **kwargs,
            )
        except AttributeError:
            self.insert_landing_data(**kwargs)

    def steps(self) -> None:
        """executes etl steps"""
        self.insert_landing_data()
        return self.main_data

    @staticmethod
    def to_csv(data_dict: dict[str:DataFrame], dirpath: Path | Directory) -> None:
        """writes dataframes to csv"""
        if isinstance(dirpath, Directory):
            path = dirpath.path
        elif isinstance(dirpath, Path):
            path = dirpath
        else:
            raise TypeError(f"got {dirpath} but need path/directory")
        env = chkenv("environment", need=None)
        if env:
            env = env + "_"
        else:
            env = ""
        for name, df in data_dict.items():
            csv_path = path / (env + name + ".csv")
            df.to_csv(csv_path, index=False)

    def main_to_csv(self, dirpath: Path | Directory) -> None:
        """writes main data to csv"""
        LocalETL.to_csv(self.main_data, dirpath)
