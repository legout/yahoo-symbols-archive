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

import datetime as dt
import sqlite3
import typing
from itertools import product
from pathlib import Path
from string import ascii_lowercase, digits

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import typer
from loguru import logger
from yfin.symbols import lookup_search, validate

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
    logger.info(f"Saving {len(results)} symbols. Start.")
    if as_ == "parquet" or as_ == "arrow" or as_ == "csv":
        table = pa.Table.from_pandas(results, preserve_index=False)
        ds.write_dataset(
            table,
            path,
            partitioning=["type"],
            format=as_,
            create_dir=True,
            existing_data_behavior="overwrite_or_ignore",
            basename_template="data_{}_part-{{i}}.{}".format(
                dt.datetime.now().date(), as_
            ),
        )

    elif as_ == "sqlite" or as_ == "sqlite3" or as_ == "sql":
        con = sqlite3.connect(path + "/symbols.sqlite")
        results.to_sql("symbols", if_exists="replace", index=False, con=con)
        con.close()

    logger.success(f"Saving {len(results)} symbols. Finished.")


def _get_lookup(
    lookup_query: typing.List[str],
    type_: str,
    *args,
    **kwargs,
) -> pd.DataFrame:
    """Get results for the given lookupquery.
    Args:
        lookup_query (list): list with query strings to lookup
        type_ (str): asset type. Have to be one or `equity`, `etf`, `cryptocurrency`, `future`,
            `index`, `mutualfund`, `currency`

    Returns:
        pd.DataFrame: _description_
    """

    if isinstance(lookup_query, str):
        logger.info(f"search for '{lookup_query}' of type {type_}")
    else:
        logger.info(
            f"search for '{lookup_query[0]} - {lookup_query[-1]}' of type {type_}"
        )

    lres = lookup_search(query=lookup_query, type_=type_, *args, **kwargs)

    logger.success(
        f"Found {len(lres)} symbols for queries from '{lookup_query[0]} to '{lookup_query[-1]}'"
    )

    return lres


def download(
    max_combination_length: int = 2,
    type_: str = "equity",
    random_proxy: bool = False,
    verbose: bool = True,
    validation: bool = True,
    remove_empty_names: bool = True,
) -> pd.DataFrame:
    """Generates all possible combinations from ascii letters, numers, "." and "="
    with a length up to `max_query_length` and fetches the results from the
    yahoo finance symbol lookup endpoint.

    Args:
        max_combination_length (int, optional): maximum combination length . Defaults to 2.
        type_ (str, optional): Choose one type from `equity, mutualfund, etf,
            index, future, currency, cryptocurrency`. Defaults to "equity".
        random_proxy (bool, optional):
            Use this flag to use a random proxy for each request. Currently a list of free proxies is used.
            Defaults to False.
        verbose (bool, optional): Wheter to show a progressbar or not. Defaults to True.
        validation (bool, optional): Run a final validation of the downloaded symbols. Defaults to True.
        remove_empty_names (bool, optional): Remove search results with empty (nan) names from the download results.

    Returns:
        pd.DataFrame: symbols
    """

    letters = list(ascii_lowercase)
    numbers = list(digits)
    samples = letters + numbers + [".", "-"]

    queries = [
        "".join(q)
        for ql in range(1, max_combination_length + 1)
        for q in list(product(*[samples for n in range(ql)]))
    ]

    res = pd.DataFrame()
    for n in range(len(queries) // 500 + 1):
        _queries = queries[n * 500 : (n + 1) * 500]

        res_ = _get_lookup(
            lookup_query=_queries,
            type_=type_,
            random_proxy=random_proxy,
            verbose=verbose,
        )
        if res_.shape[0] > 0:
            if validation:
                logger.info(f"Validation of {len(res_)} symbols.")
                val_res = validate(
                    res_["symbol"].tolist(),
                    max_symbols=750,
                    verbose=verbose,
                ).reset_index(drop=True)

                res_ = res_.merge(val_res, on=["symbol"])

            res = pd.concat([res, res_]).drop_duplicates()

            if remove_empty_names:
                res = res[~res["name"].isna()]

    return res


@app.command()
def main(
    max_combination_length: int = 2,
    types: str = "equity",
    random_proxy: bool = False,
    verbose: bool = True,
    validation: bool = True,
    remove_empty_names: bool = True,
    output: str = "./db",
    output_type: str = "parquet",
):
    """Generates all possible combinations from ascii letters, numbers, "." and "="
    with a length of up to `max_query_length` and fetches the results from the
    yahoo finance symbol lookup endpoint and finally saves the results into a
    `parquet` dataset, `csv` files or `sqlite3` database.

    Args:
        max_combination_length (int, optional): maximum combination length . Defaults to 2.
        types (str, optional): Choose one or more types from `equity, mutualfund, etf,
            index, future, currency, cryptocurrency`. Defaults to "equity".
        random_proxy (bool, optional):
            Use this flag to use a random proxy for each request. Currently a list of free proxies is used.
            Defaults to False.
        verbose (bool, optional): Wheter to show a progressbar or not. Defaults to True.
        validation (bool, optional): Run a finally validation of the downloaded symbols. Defaults to True.
        remove_empty_names (bool, optional): Remove search results with empty (nan) names from the download results.
        output (str, optional): storage path. Defaults to "./db".
        output_type (str, optional): storage type. Defaults to "parquet".
    """
    if isinstance(types, str):
        types = [types]

    for type_ in types:

        results = download(
            max_combination_length=max_combination_length,
            type_=type_,
            random_proxy=random_proxy,
            verbose=verbose,
            validation=validation,
            remove_empty_names=remove_empty_names,
        )

        save(results=results, path=output, as_=output_type)


if __name__ == "__main__":
    app()
