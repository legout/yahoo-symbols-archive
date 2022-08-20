#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
@File    :   download.py
@Time    :   2022/08/18 20:28:38
@Author  :   Volker Lorrmann
@Version :   0.1
@Contact :   volker.lorrmann@gmail.com
@License :   (C)Copyright 2020-2022, Volker Lorrmann
@Desc    :   None
"""

import typer
from yahoo_symbols.yahoo_symbols import YahooSymbols
from yahoo_symbols.yahoo_symbols import validate as validate_
import asyncio
import pandas as pd
import pyarrow as pa
import pyarrow
import pyarrow.dataset as ds
from pathlib import Path
import sqlite3


app = typer.Typer()


def save(
    results: pd.DataFrame,
    path: str,
    as_="parquet",
):
    """Save the symbol results dataframe to the given `path` as `parquet`
    dataset, into `csv` files or a `sqlite3` database.

    Args:
        results (pd.DataFrame): symbols
        path (str): storage path
        as_ (str, optional): storage type. Defaults to "parquet".
    """

    if as_ == "parquet" or as_ == "arrow" or as_ == "csv":
        table = pa.Table.from_pandas(results, preserve_index=False)
        ds.write_dataset(
            table,
            path,
            partitioning=["type", "exchange"],
            format=as_,
            create_dir=True,
        )

    # elif as_ == "csv" or as_ == "text":
    #     for type_ in results["type"].unique():
    #         results_ = results.query(f"type=='{type_}'")
    #         for exchange in results_["exchange"].unique():
    #             Path(path + f"/{type_}/{exchange}").mkdir(parents=True, exist_ok=True)
    #             results_.query(f"exchange=='{exchange}'").to_csv(
    #                 path + f"/{type_}/{exchange}/symbols.csv", index=False
    #             )

    elif as_ == "sqlite" or as_ == "sqlite3" or as_ == "sql":
        con = sqlite3.connect(path + "/symbols.sqlite")
        results.to_sql("symbols", if_exists="replace", index=False, con=con)
        con.close()


def download(
    max_combination_length: int = 2,
    types: str = "equity",
    limits_per_host: int = 50,
    semaphore: int = 25,
    use_random_proxy: bool = False,
    verbose: bool = True,
    validate: bool = True,
) -> pd.DataFrame:
    """Generates all possible combinations from ascii letters, numers, "." and "="
    with a length up to `max_query_length` and fetches the results from the
    yahoo finance symbol lookup endpoint.

    Args:
        max_combination_length (int, optional): maximum combination length . Defaults to 2.
        types (str, optional): Can be anyone or a combination of `equity, mutualfund, etf,
            index, future, currency, cryptocurrency`. Defaults to "equity".
        limits_per_host (int, optional):  Is used to limit the number of parallel requests.
            Should be a value between 10 and 100.. Defaults to 50.
        semaphore (int, optional): Is used to limit the number of parallel requests.
            Should be between smaller than `limits-per-host`.. Defaults to 25.
        use_random_proxy (bool, optional):
            Use this flag to use a random proxy for each request. Currently a list of free proxies is used.
            Defaults to False.
        verbose (bool, optional): Wheter to show a progressbar or not. Defaults to True.
        validate (bool, optional): Run a finally validation of the downloaded symbols. Defaults to True.

    Returns:
        pd.DataFrame: symbols
    """

    ys = YahooSymbols()

    query_lengths = range(1, max_combination_length + 1)
    types = types.split(",")

    results = pd.DataFrame()
    for type_ in types:
        for query_length in query_lengths:
            res_ = asyncio.run(
                ys.lookup(
                    query_length=query_length,
                    type_=type_,
                    limits_per_host=limits_per_host,
                    semaphore=semaphore,
                    use_random_proxy=use_random_proxy,
                    verbose=verbose,
                )
            )
            results = pd.concat(
                [results, res_.drop_duplicates(subset=["symbol", "exchange"])],
                ignore_index=True,
            )

    results = results.rename(
        {"shortName": "name", "quoteType": "type", "industryName": "industry"}, axis=1
    ).drop_duplicates(subset=["symbol", "exchange"])[
        ["symbol", "name", "exchange", "type", "industry"]
    ]
    if validate:
        validation = validate_(
            results["symbol"].tolist(),
            max_symbols=750,
            limits_per_host=10,
            semaphore=5,
            verbose=verbose,
        ).reset_index()

        results = results.merge(validation, on=["symbol"])

    return results


@app.command()
def main(
    max_combination_length: int = 2,
    types: str = "equity",
    limits_per_host: int = 50,
    semaphore: int = 25,
    use_random_proxy: bool = False,
    verbose: bool = True,
    validate: bool = True,
    output: str = "./db",
    output_type: str = "parquet",
):
    """Generates all possible combinations from ascii letters, numers, "." and "="
    with a length up to `max_query_length` and fetches the results from the
    yahoo finance symbol lookup endpoint and finally saves the results into a
    `parquet` dataset, `csv` files or `sqlite3` database.

    Args:
        rgs:
        max_combination_length (int, optional): maximum combination length . Defaults to 2.
        types (str, optional): Can be anyone or a combination of `equity, mutualfund, etf,
            index, future, currency, cryptocurrency`. Defaults to "equity".
        limits_per_host (int, optional):  Is used to limit the number of parallel requests.
            Should be a value between 10 and 100.. Defaults to 50.
        semaphore (int, optional): Is used to limit the number of parallel requests.
            Should be between smaller than `limits-per-host`.. Defaults to 25.
        use_random_proxy (bool, optional):
            Use this flag to use a random proxy for each request. Currently a list of free proxies is used.
            Defaults to False.
        verbose (bool, optional): Wheter to show a progressbar or not. Defaults to True.
        validate (bool, optional): Run a finally validation of the downloaded symbols. Defaults to True.
        output (str, optional): storage path. Defaults to "./db".
        output_type (str, optional): storage type. Defaults to "parquet".
    """

    results = download(
        max_combination_length=max_combination_length,
        types=types,
        limits_per_host=limits_per_host,
        semaphore=semaphore,
        use_random_proxy=use_random_proxy,
        verbose=verbose,
        validate=validate,
    )

    save(results=results, path=output, as_=output_type)


if __name__ == "__main__":
    app()
