# Yahoo Symbols Downloader

This is a blazing fast python script to download *almost all* yahoo symbols.


## Install

```
pip install git+https://github.com/legout/yahoo-symbols.git
```

## Usage Example

```
python -m yahoo_symbols.download --max-combination-length=3 --type=equity,etf --output=./database --output-type=parquet
``` 

## Options

```
Usage: download.py [OPTIONS]

Options:
  --max-combination-length INTEGER The maximum length of combinations to search for. 
                                   Higher numbers may result in more results at cost of longer download times.
                                   [default: 2]
  --types TEXT                     Choose one or several types. 
                                   Available types are  `equity, mutualfund, etf, index, future, currency, cryptocurrency`
                                   [default: equity]
  --random-proxy / --use-random-proxy
                                   Use a random proxy for each request. Currently only proxies from webshare are supported.
                                   [default: no-random-proxy]
  --verbose / --no-verbose         Wheter to show a progressbar or not. [default: verbose]
  -validation /--no-validation     Run a finally validation of the downloaded symbols. [default: validate]
  --output TEXT                    The output path where the downloaded symbols are saved to. [default: ./db]
  --output-type TEXT               Defines the output type. Options are `parquet`, `csv` or `sqlite3`. [default: parquet]
  --help                           Show this message and exit.
```


<hr>

## Tips
### Number of requests

The benchmarks of this script for one asset type are (tested for type `equity`):

| max query length             | 1    | 2     | 3      | 4       |
| ---------------------------- | ---- | ----- | ------ | ------- |
| number of requests           | 38   | 1482  | 56354  | 2141490 |
| estimated download duration* | ~ 3s | ~1min | ~10min | ~3h     |


### Best practice
 - You´ll get the best results (most unique symbols) from the symbol downloads if you run this script seperatly for each type (equity, etf,...).
 - The option `--max-query-length` should be `2`or `3`. 

### Use of a random proxy server.

**Note**
This script should work fine without using random proxies.

When using the  option `--use-random-proxy`  free proxies* are used. In my experience, these proxies are not reliable, but maybe you are lucky.

#### Webshare.io proxies
I am using proxies from [webshare.io](https://www.webshare.io/). I am very happy with their service and the pricing. If you wanna use their service too, sign up (use the [this link](https://www.webshare.io/?referral_code=upb7xtsy39kl) if you wanna support my work) and choose a plan that fits your needs. In the next step, go to Dashboard -> Proxy -> List -> Download and copy the download link. Place this download link into an `.env` file and name the variable `WEBSHARE_PROXIES_URL` (see the `.env-exmaple` in this repository).



```
WEBSHARE_PROXIES_URL="https://proxy.webshare.io/api/v2/proxy/list/download/abcdefg1234567/-/any/username/direct/-/"
```

*Free Proxies are scraped from here:
- "http://www.free-proxy-list.net"
- "https://free-proxy-list.net/anonymous-proxy.html"
- "https://www.us-proxy.org/"
- "https://free-proxy-list.net/uk-proxy.html"
- "https://www.sslproxies.org/"


<hr>

#### Support my work :-)

If you find this useful, you can buy me a coffee. Thanks!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W0ACJPB)


