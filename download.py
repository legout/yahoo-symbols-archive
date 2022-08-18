#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   download.py
@Time    :   2022/08/18 20:28:38
@Author  :   Volker Lorrmann
@Version :   0.1
@Contact :   volker.lorrmann@gmail.com
@License :   (C)Copyright 2020-2022, Volker Lorrmann
@Desc    :   None
'''

import typer
from yahoo_symbols.yahoo_symbols import YahooSymbols
import asyncio
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import json
from pathlib import Path
import sqlite3


app = typer.Typer()


def save(results: pd.DataFrame, path: str, as_="parquet"):

    if as_ == "parquet":
        table = pa.Table.from_pandas(results, preserve_index=False)
        ds.write_dataset(
            table,
            path,
            partitioning=["type", "exchange"],
            
            partitioning_flavor="filename",
            format="parquet",
            create_dir=True,
        )

    elif as_ == "csv":
        for type_ in results["type"].unique():
            results_ = results.query(f"type=='{type_}'")
            for exchange in results_["exchange"].unique():
                Path(path + f"/{type_}/{exchange}").mkdir(parents=True, exist_ok=True)
                results_.query(f"exchange=='{exchange}'").to_csv(
                    path + f"/{type_}/{exchange}/symbols.csv", index=False
                )

    elif as_ == "sqlite":
        con = sqlite3.connect(path + "/symbols.sqlite")
        results.to_sql("symbols", if_exists="replace", index=False, con=con)
        con.close()


def download(
    max_query_length: int = 1,
    types: str = "equity",
    limits_per_host: int = 50,
    semaphore: int = 20,
    use_random_proxy: bool = False,
    verbose: bool = True,
):

    ys = YahooSymbols()

    query_lengths = range(1, max_query_length + 1)
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

    return results


@app.command()
def main(
    max_query_length: int = 1,
    types: str = "equity",
    limits_per_host: int = 50,
    semaphore: int = 20,
    use_random_proxy: bool = False,
    verbose: bool = True,
    output: str = "./db",
    as_: str = "parquet",
):

    results = download(
        max_query_length=max_query_length,
        types=types,
        limits_per_host=limits_per_host,
        semaphore=semaphore,
        use_random_proxy=use_random_proxy,
        verbose=verbose,
    )

    save(results=results, path=output, as_=as_)


if __name__ == "__main__":
    app()
