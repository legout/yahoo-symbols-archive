# Yahoo Symbols Downloader

This is a blazing fast python script to download *almost all* yahoo symbols.


## Install

Clone this repository or download the zip archive.

```
git clone https://github.com/legout/yahoo-symbols.git
```

Install requirements
```
cd yahoo-symbols

pip install -r requirements.txt
```

## Usage Example

```
python download.py --max-query-length=3 --type=equity,etf --output=./database --output-type=csv
``` 

## Options

```
Usage: download.py [OPTIONS]

Options:
  --max-query-length INTEGER      The maximum length of combinations to search for. 
                                  Higher numbers may result in more results at cost of longer download times.
                                  [default: 2]
  --types TEXT                    Can be anyone or a combination of `equity, mutualfund, etf, index, future, currency, cryptocurrency`
                                  [default: equity]
  --limits-per-host INTEGER       Is used to limit the number of parallel requests. Should be a value between 10 and 100.
                                  [default: 50]
  --semaphore INTEGER             Is used to limit the number of parallel requests.  Should be between smaller than `limits-per-host`.
                                  [default: 25]
  --use-random-proxy / --no-use-random-proxy
                                  Use this flag to use a random proxy for each request. Currently a list of free proxies is used. 
                                  In most cases these proxies aren´t relaible. You can provide a list of your own proxies in `async_requests/config.py`.
                                  [default: no-use-random-proxy]
  --verbose / --no-verbose        Wheter to show a progressbar or not. [default: verbose]
  --output TEXT                   The output path where the downloaded symbols are saved to. [default: ./db]
  --output-type TEXT              Defines the output type. Options are `parquet`, `csv` or `sqlite3`. [default: parquet]
  --help                          Show this message and exit.
```




<hr>

## Tips
### Number of requests

| max query length               | 1  | 2       | 3      | 4       |
|--------------------------------|----|---------|--------|---------|
| number of requests             | 38 | 1482    | 56354  | 2141490 |
| estimated download duration*   | ~ 3s | ~1min | ~10min | ~3h     | 

*depends on your internet connectivity, and the options `--limits-per-host` and `--semaphore`

### Best practice
 - You´ll get the best results (most unique symbols) from the symbol downloads if you run this script seperatly for each type (equity, etf,...).
 - The option `--max-query-length` should be `2`or `3`. 

### Use of a random proxy server.

**Note**
This script should work fine without random proxies.


Currently, the  option `--use-random-proxy` uses free proxies, which aren´t reliable in most cases. Instead you should use your own proxies. You can set your own proxy list in the file `async_requests/config.py`. Simply add the parameter `PROXIES` to the end of the file.

```
...
else:
    PROXIES = get_free_proxy_list()
    
# Add your list of proxies manually here
# PROXIES = ["http://my-own-proxy-1.abc:1234", "http://my-own-pwoxy-2.cdf:9876"]

```

A very fast and affordable provider of proxy servers is [webshare.io](https://webshare.io). If you have subscribed to their service, you can place your personal proxy list url into the file `async_requests/config.py`. You can find the url in your webshare.io settings.  "Settings->Proxy->List->Export".

```
...
# Place your proxy list url from webshare.io here
URL_WEBSHARE_PROXY_LIST = None  <-- PLACE URL HERE

if URL_WEBSHARE_PROXY_LIST is not None:
    PROXIES = get_webshare_proxy_list(URL_WEBSHARE_PROXY_LIST)
...
```


<hr>

#### Support me :-)

If you find this useful, you can buy me a coffee. Thanks!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W0ACJPB)


