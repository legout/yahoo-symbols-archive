#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   async_requests.py
@Time    :   2022/08/18 20:29:03
@Author  :   Volker Lorrmann
@Version :   0.1
@Contact :   volker.lorrmann@gmail.com
@License :   (C)Copyright 2020-2022, Volker Lorrmann
@Desc    :   None
'''


import asyncio
import aiohttp
import backoff
import progressbar
import typing as tp
from .utils import random_user_agent, random_proxy
from .config import USER_AGENTS, PROXIES


def _to_list(x: list | str) -> list:
    if isinstance(x, (str, dict)):
        return [x]
    elif x is None:
        return [None]
    else:
        return x


def _extend_list(x: list, max_len: int) -> list:
    if len(x) == 1:
        return x * max_len
    else:
        return x


class AsyncRequests:
    """A class used for asynchronous Http Requests."""

    def __init__(
        self,
        headers: dict | None = None,
        semaphore: int = 10,
        timeout: int = 120,
        limits_per_host: int = 10,
        use_random_proxy: bool = False,
    ):
        """
        Args:
            headers (dict | None, optional): The request headers. Defaults to None.
            semaphore (int, optional): The number of semaphores. Defaults to None.
            timeout (int, optional): The request timeout. Defaults to None.
            limits_per_host (int, optional): The limit number per host. Defaults to None.
            use_random_proxy (bool, optional): Use a random proxy from list of proxies. Defaults to False.
        """
        self._semaphore = semaphore
        self._timeout = timeout
        self._limits_per_host = limits_per_host
        self._headers = headers
        self._use_random_proxy = use_random_proxy

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientError,
        max_time=60,
        max_tries=3,
    )
    async def _request(
        self,
        method: str,
        session: aiohttp.client.ClientSession,
        url: str,
        params: dict,
        data: dict,
        json: str,
        key: str,
        parse_func: tp.Callable,
        return_type: str = "json",
        proxy: str | None = None,
    ) -> tp.Union[dict, str, bytes]:

        if self._headers is None:
            headers = random_user_agent(USER_AGENTS)
        else:
            headers = self._headers

        if self._use_random_proxy:
            proxy = random_proxy(PROXIES)

        async with self._sema, session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            proxy=proxy,
        ) as response:
            if response.status >= 400:
                raise aiohttp.ClientError(response.status)
            elif response.status >= 500:
                raise aiohttp.ServerConnectionError(response.status)
            if return_type == "json":
                result = await response.json(content_type=None)

            elif return_type == "text":
                result = await response.text()
            else:
                result = await response.read()

            if parse_func is not None:

                return (
                    await parse_func(key, result)
                    if key is not None
                    else await parse_func(result)
                )
            else:
                return {key: result} if key is not None else result

    async def requests(
        self,
        url: tp.Union[str, tuple, list],
        params: tp.Union[dict, tuple, list, None] = None,
        data: tp.Union[dict, tuple, list, None] = None,
        json: tp.Union[dict, tuple, list, None] = None,
        headers: tp.Union[dict, None] = None,
        proxy: tp.Union[str, None] = None,
        key: tp.Union[str, int, tuple, list, None] = None,
        parse_func: object = None,
        method: str = "GET",
        return_type: str = None,
        ssl: bool = False,
        verbose: bool = False,
    ) -> dict | list:
        """Executes asyncronous requests.

        Args:
            url (tp.Union[str, tuple, list]): The request url.
            params (tp.Union[dict, tuple, list, None], optional): The request parameter. Defaults to None.
            data (tp.Union[dict, tuple, list, None], optional): The request data. Defaults to None.
            json (tp.Union[dict, tuple, list, None], optional): The request json object. Defaults to None.
            headers (tp.Union[dict, None], optional): The request headers. Defaults to None.
            proxy (tp.Union[str,None], optional): Use the given proxy. Defaults to None.
            key (tp.Union[str, int, tuple, list, None], optional): A key to assign the request responses. Defaults to None.
            parse_func (object, optional): A function for parsing the request responses. Defaults to None.
            method (str, optional): The request method. Defaults to "GET".
            return_type (str, optional): Defines return rype. Defaults to None.
            ssl (bool, optional): Use ssl or not. Defaults to False.
            verbose (bool, optional): If True, a progressbar is displayed. Defaults to False.

        Returns:
            dict: Dictionary with the request response.
        """
        if headers is not None:
            self._headers = headers

        url = _to_list(url)
        params = _to_list(params)
        data = _to_list(data)
        json = _to_list(json)
        key = _to_list(key)

        max_len = max([len(url), len(params), len(data), len(json), len(key)])

        url = _extend_list(url, max_len)
        params = _extend_list(params, max_len)
        data = _extend_list(data, max_len)
        json = _extend_list(json, max_len)
        key = _extend_list(key, max_len)

        timeout = aiohttp.ClientTimeout(total=self._timeout)
        conn = aiohttp.TCPConnector(
            limit_per_host=self._limits_per_host, verify_ssl=ssl
        )
        self._sema = asyncio.Semaphore(self._semaphore)

        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            tasks = [
                asyncio.create_task(
                    self._request(
                        method=method,
                        session=session,
                        url=url[n],
                        params=params[n],
                        data=data[n],
                        json=json[n],
                        proxy=proxy,
                        key=key[n],
                        parse_func=parse_func,
                        return_type=return_type,
                    )
                )
                for n in range(len(url))
            ]

            if verbose:
                results = [
                    await task
                    for task in progressbar.progressbar(
                        asyncio.as_completed(tasks), max_value=len(url)
                    )
                ]

            else:
                results = [await task for task in asyncio.as_completed(tasks)]

        if key[0] is not None and isinstance(results, dict):
            results = dict((k, _results[k]) for _results in results for k in _results)

        if key[0] is not None and isinstance(results[0], dict):
            results = dict((k, _results[k]) for _results in results for k in _results)

        if len(url) == 1 and isinstance(results, (list, tuple)):
            results = results[0]

        return results

    def run_requests(self, *args, **kwargs):
        """Executes asyncronous requests."""

        return asyncio.run(self.requests(*args, **kwargs))


async def async_requests(
    url: tp.Union[str, tuple, list],
    headers: dict = None,
    params: tp.Union[dict, tuple, list, None] = None,
    data: tp.Union[dict, tuple, list, None] = None,
    json: tp.Union[dict, tuple, list, None] = None,
    key: tp.Union[str, int, tuple, list, None] = None,
    parse_func: object = None,
    method: str = "GET",
    return_type: str = "json",
    ssl: bool = False,
    verbose: bool = False,
    semaphore: int = 10,
    timeout: int = 120,
    limits_per_host: int = 10,
    use_random_proxy: bool = False,
) -> dict:
    """A function for asynchronous Http requests.

    Args:
        url (tp.Union[str, tuple, list]): The request url.
        params (tp.Union[dict, tuple, list, None], optional): The request parameter. Defaults to None.
        data (tp.Union[dict, tuple, list, None], optional): The request data. Defaults to None.
        json (tp.Union[dict, tuple, list, None], optional): The request json object. Defaults to None.
        headers (dict, optional): The request headers. Defaults to None.
        key (tp.Union[str, int, tuple, list, None], optional): A key to assign the request responses. Defaults to None.
        parse_func (object, optional): A function for parsing the request responses. Defaults to None.
        method (str, optional): The request method. Defaults to "GET".
        return_type (str, optional): Defines return rype. Defaults to json.
        ssl (bool, optional): Use ssl or not. Defaults to False.
        verbose (bool, optional): If True, a progressbar is displayed. Defaults to False.
        semaphore (int, optional): The number of semaphores. Defaults to None.
        timeout (int, optional): The request timeout. Defaults to None.
        limits_per_host (int, optional): The limit number per host. Defaults to None.
        use_random_proxy (bool, optional): Use a random proxy from list of proxies. Defaults to False.

    Returns:
        Returns:
            dict: Dictionary with the request response.
    """
    ar = AsyncRequests(
        headers=headers,
        semaphore=semaphore,
        timeout=timeout,
        limits_per_host=limits_per_host,
        use_random_proxy=use_random_proxy,

    )
    return await ar.requests(
        url=url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        #proxy=proxy,
        key=key,
        parse_func=parse_func,
        method=method,
        return_type=return_type,
        ssl=ssl,
        verbose=verbose,
    )


def requests(
    url: tp.Union[str, tuple, list],
    headers: dict = None,
    params: tp.Union[dict, tuple, list, None] = None,
    data: tp.Union[dict, tuple, list, None] = None,
    json: tp.Union[dict, tuple, list, None] = None,
    key: tp.Union[str, int, tuple, list, None] = None,
    parse_func: object = None,
    method: str = "GET",
    return_type: str = "json",
    ssl: bool = False,
    verbose: bool = False,
    semaphore: int = 10,
    timeout: int = 120,
    limits_per_host: int = 10,
    use_random_proxy: bool = False,
) -> dict:
    """A function for asynchronous Http requests.

    Args:
        url (tp.Union[str, tuple, list]): The request url.
        params (tp.Union[dict, tuple, list, None], optional): The request parameter. Defaults to None.
        data (tp.Union[dict, tuple, list, None], optional): The request data. Defaults to None.
        json (tp.Union[dict, tuple, list, None], optional): The request json object. Defaults to None.
        headers (dict, optional): The request headers. Defaults to None.
        key (tp.Union[str, int, tuple, list, None], optional): A key to assign the request responses. Defaults to None.
        parse_func (object, optional): A function for parsing the request responses. Defaults to None.
        method (str, optional): The request method. Defaults to "GET".
        return_type (str, optional): Defines return rype. Defaults to json.
        ssl (bool, optional): Use ssl or not. Defaults to False.
        verbose (bool, optional): If True, a progressbar is displayed. Defaults to False.
        semaphore (int, optional): The number of semaphores. Defaults to None.
        timeout (int, optional): The request timeout. Defaults to None.
        limits_per_host (int, optional): The limit number per host. Defaults to None.
        use_random_proxy (bool, optional): Use a random proxy from list of proxies. Defaults to False.
        proxy (tp.Union[str,None], optional): Use the given proxy. Defaults to None.

    Returns:
        Returns:
            dict: Dictionary with the request response.
    """
    ar = AsyncRequests(
        headers=headers,
        semaphore=semaphore,
        timeout=timeout,
        limits_per_host=limits_per_host,
        use_random_proxy=use_random_proxy,
    )
    return ar.run_requests(
        url=url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        key=key,
        parse_func=parse_func,
        method=method,
        return_type=return_type,
        ssl=ssl,
        verbose=verbose,
    )
