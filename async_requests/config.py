from .utils import get_user_agents, get_webshare_proxy_list, get_free_proxy_list

USER_AGENTS = get_user_agents()
URL_WEBSHARE_PROXY_LIST = None

if URL_WEBSHARE_PROXY_LIST is not None:
    PROXIES = get_webshare_proxy_list(URL_WEBSHARE_PROXY_LIST)
    
else:
    PROXIES = get_free_proxy_list()