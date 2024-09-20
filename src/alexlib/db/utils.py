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

from queue import Queue
from sqlite3 import Connection as SqliteConnection
from threading import Thread

from pandas import DataFrame
from sqlalchemy import Engine

from alexlib.files.objects import File


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
