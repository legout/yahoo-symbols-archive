#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   utils.py
@Time    :   2022/08/18 20:29:23
@Author  :   Volker Lorrmann
@Version :   0.1
@Contact :   volker.lorrmann@gmail.com
@License :   (C)Copyright 2020-2022, Volker Lorrmann
@Desc    :   None
'''

import random
import requests
import pandas as pd

def get_user_agents():
    return requests.get(
        "https://gist.githubusercontent.com/pzb/b4b6f57144aea7827ae4/raw/cf847b76a142955b1410c8bcef3aabe221a63db1/user-agents.txt"
    ).text.split("\n")
 

def random_user_agent(user_agents:list, as_dict: bool = True) -> str:
    """Random user-agent from list USER_AGENTS.

    Returns:
        str: user-agent
    """

    user_agent = random.choice(user_agents)

    if as_dict:
        return {"user-agent": user_agent}
    else:
        return user_agent


def random_proxy(proxies: list | None = None) -> str:
    if proxies is None:
        return None
    else:
        if isinstance(proxies, str):
            return proxies
        else:
            return random.choice(proxies)


def get_webshare_proxy_list(url: str) -> list:
    """Fetches a list of fast and affordable proxy servers from http://webshare.io.

    After subsription for a plan, get the export url for your proxy list.
        Settings -> Proxy -> List -> Export
    """
    proxies = [p for p in requests.get(url).text.split("\r\n") if len(p) > 0]
    proxies = [
        dict(zip(["ip", "port", "user", "pw"], proxy.split(":"))) for proxy in proxies
    ]
    proxies = [
        f"http://{proxy['user']}:{proxy['pw']}@{proxy['ip']}:{proxy['port']}"
        for proxy in proxies
    ]
    return proxies


def get_free_proxy_list() -> list:
    urls = [
        "http://www.free-proxy-list.net",
        "https://free-proxy-list.net/anonymous-proxy.html",
        "https://www.us-proxy.org/",
        "https://free-proxy-list.net/uk-proxy.html",
        "https://www.sslproxies.org/",
    ]

    proxies = list()
    for url in urls:
        proxies.append(
            pd.read_html(requests.get(url, headers={"user-agent":"yahoo-symbols-async-requests"}).text)[0]
            .rename({"Last Checked": "LastChecked"}, axis=1)
            .query("LastChecked.str.contains('secs') & Https=='no'")
        )

    proxies = pd.concat(proxies, ignore_index=True)
    proxies = (
        proxies.iloc[:, :2]
        .astype(str)
        .apply(lambda x: "http://"+":".join(x.tolist()), axis=1)
        .tolist()
    )
    return proxies

#
