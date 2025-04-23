from typing import List, Dict, Set, Optional, Iterator, Any, Union
from concurrent.futures import ThreadPoolExecutor, Future
from bs4 import BeautifulSoup
import requests
from requests.models import Response
from rich import print
from itertools import cycle
import json
import os
import re
from urllib.parse import urlparse
import random
import threading
import time

ProxyString = str
SourceUrl = str
JsonDict = Dict[str, Any]

class ProxyManager:
    def __init__(self, max_proxies_per_source: int = 100, auto_refresh: bool = True, refresh_interval: int = 120, max_threads: int = 100) -> None:
        self.max_proxies_per_source: int = max_proxies_per_source
        self.auto_refresh: bool = auto_refresh
        self.refresh_interval: int = refresh_interval
        self.max_threads: int = max_threads
        self.proxies: List[ProxyString] = self._load_proxies()
        self.proxy_cycle: Iterator[ProxyString] = cycle(self.proxies)
        self.refresh_timer: Optional[threading.Timer] = None

        print(f"[bold green]Found {len(self.proxies)} working proxies[/bold green]")
        
        if self.auto_refresh:
            self.refresh_timer = threading.Timer(self.refresh_interval, self._auto_refresh)
            self.refresh_timer.start()

    def _load_proxies(self) -> List[ProxyString]:
        working_proxies: Set[ProxyString] = set()

        # GitHub proxy sources
        github_sources: List[SourceUrl] = [
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
            'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt',
            'https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/rx443/proxy-list/main/online/http.txt',
            'https://raw.githubusercontent.com/almroot/proxylist/master/list.txt',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            'https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt',
            'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
            'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
            'https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt',
            'https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/cnfree.txt',
            'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt',
            'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt',
            'https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/Volodichev/proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt',
            'https://raw.githubusercontent.com/Zaeem20/FREE_PROXY_LIST/master/http.txt',
            'https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/ObcbO/getproxy/master/http.txt',
            'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt',
            'https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt',
            'https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt',
            'https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt',
            'https://raw.githubusercontent.com/hanwayTech/free-proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/hanwayTech/free-proxy-list/main/https.txt',
            'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt',
        ]

        # API proxy sources
        api_sources: List[SourceUrl] = [
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http',
            'https://www.proxy-list.download/api/v1/get?type=https',
            'https://api.proxyscrape.com/?request=displayproxies&protocol=http',
            'http://spys.me/proxy.txt',
            'https://api.proxyscan.io/v1/proxies?protocol=http',
            'https://proxylist.geonode.com/api/proxy-list?protocol=http&sort_by=lastChecked&sort_type=desc&filterUpTime=90&page=1&limit=100',
            'https://pubproxy.com/api/proxy?limit=100&format=txt&type=http',
            'https://www.proxyscan.io/api/proxy?format=txt&type=http',
            'https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list',
            'https://api.openproxylist.xyz/http.txt',
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            'https://www.proxy-list.download/api/v1/get?type=http&anon=elite',
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=anonymous',
            'https://openproxylist.xyz/http.txt',
            'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.json',
            'https://proxylist.icu/proxy/',
            'https://www.proxyscan.io/download?type=http',
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
        ]

        # Web scraping sources
        scrape_sources: List[SourceUrl] = [
            'https://free-proxy-list.net/',
            'https://www.us-proxy.org/',
            'https://www.sslproxies.org/',
            'https://www.freeproxylists.net/http.html',
            'http://www.freeproxy.world/',
            'https://www.proxynova.com/proxy-server-list/',
            'https://www.proxyrack.com/free-proxy-list/',
            'https://www.hide-my-ip.com/proxylist.shtml',
            'http://www.httptunnel.ge/ProxyListForFree.aspx',
            'https://www.ip-adress.com/proxy-list',
            'https://proxyservers.pro/',
            'https://www.proxy-list.org/',
            'https://www.proxydocker.com/',
            'https://www.socks-proxy.net/',
            'https://www.cool-proxy.net/',
            'https://premproxy.com/list/',
            'https://www.proxy-list.download/HTTP',
            'https://www.proxyniche.com/proxy-list/',
            'http://proxydb.net/',
            'http://www.proxylists.net/',
            'http://www.megaproxy.com/freeproxy.html',
            'https://vpnoverview.com/privacy/anonymous-browsing/free-proxy-servers/',
            'https://www.freeproxylists.net/',
            'https://www.my-proxy.com/free-proxy-list.html',
            'https://www.proxyrotator.com/free-proxy-list/',
            'https://free-proxy-list.com/',
        ]

        def fetch_from_github(source: SourceUrl) -> List[ProxyString]:
            try:
                response: Response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies: List[ProxyString] = response.text.strip().split('\n')[:self.max_proxies_per_source]
                    return [proxy.strip() for proxy in proxies if proxy.strip()]
            except Exception:
                pass
            return []

        def fetch_from_api(source: SourceUrl) -> List[ProxyString]:
            try:
                response: Response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    if 'geonode' in source:
                        data: JsonDict = response.json()
                        return [f"{proxy['ip']}:{proxy['port']}" for proxy in data['data']][:self.max_proxies_per_source]
                    elif 'proxyscan' in source:
                        data: JsonDict = response.json()
                        return [f"{proxy['Ip']}:{proxy['Port']}" for proxy in data][:self.max_proxies_per_source]
                    elif 'fate0/proxylist' in source:
                        proxies: List[ProxyString] = []
                        for line in response.text.strip().split('\n'):
                            try:
                                proxy_data: JsonDict = json.loads(line)
                                proxies.append(f"{proxy_data['host']}:{proxy_data['port']}")
                            except:
                                pass
                        return proxies[:self.max_proxies_per_source]
                    elif source.endswith('.json'):
                        data: Union[List[JsonDict], JsonDict] = response.json()
                        if isinstance(data, list):
                            return [f"{proxy['ip']}:{proxy['port']}" for proxy in data][:self.max_proxies_per_source]
                        elif isinstance(data, dict) and 'proxies' in data:
                            return [f"{proxy['ip']}:{proxy['port']}" for proxy in data['proxies']][:self.max_proxies_per_source]
                    else:
                        return response.text.strip().split('\n')[:self.max_proxies_per_source]
            except Exception:
                pass
            return []

        def scrape_from_web(source: SourceUrl) -> List[ProxyString]:
            try:
                response: Response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')
                    proxies: List[ProxyString] = []

                    # Generic table scraping
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows[1:self.max_proxies_per_source+1]:  # Skip header row
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                ip = cols[0].text.strip()
                                port = cols[1].text.strip()
                                if ip and port:
                                    proxies.append(f"{ip}:{port}")

                    # Regex-based scraping
                    ip_port_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b'
                    found_proxies = re.findall(ip_port_pattern, response.text)
                    proxies.extend(found_proxies[:self.max_proxies_per_source])

                    return list(set(proxies))  # Remove duplicates
            except Exception:
                pass
            return []

        # Fetch proxies from all sources
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            github_futures: Dict[Future, SourceUrl] = {executor.submit(fetch_from_github, source): source for source in github_sources}
            api_futures: Dict[Future, SourceUrl] = {executor.submit(fetch_from_api, source): source for source in api_sources}
            scrape_futures: Dict[Future, SourceUrl] = {executor.submit(scrape_from_web, source): source for source in scrape_sources}

            for future in github_futures:
                proxies = future.result()
                for proxy in proxies:
                    if not proxy.startswith('http'):
                        proxy = f'http://{proxy}'
                    working_proxies.add(proxy)

            for future in api_futures:
                proxies = future.result()
                for proxy in proxies:
                    if not proxy.startswith('http'):
                        proxy = f'http://{proxy}'
                    working_proxies.add(proxy)

            for future in scrape_futures:
                proxies = future.result()
                for proxy in proxies:
                    if not proxy.startswith('http'):
                        proxy = f'http://{proxy}'
                    working_proxies.add(proxy)

        # Fallback proxies in case all sources fail
        fallback_proxies: List[ProxyString] = [
            'http://163.172.31.44:80',
            'http://20.111.54.16:8123',
            'http://51.159.115.233:3128',
            'http://198.11.175.192:8080',
            'http://165.225.38.68:10605',
            'http://165.225.38.94:10605',
            'http://165.225.38.32:10605',
            'http://165.225.38.99:10605',
            'http://104.129.196.50:10605',
            'http://104.129.196.81:10605'
        ]

        # Verify proxies using ThreadPoolExecutor
        verified_proxies: List[ProxyString] = []
        print("[yellow]Verifying proxies...[/yellow]")

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures: Dict[Future, ProxyString] = {executor.submit(self._check_proxy, proxy): proxy for proxy in working_proxies}
            for future in futures:
                proxy = futures[future]
                if future.result():
                    verified_proxies.append(proxy)
                    print(f"[green]Verified working proxy: {proxy}[/green]")

        # Add fallback proxies if we don't have enough verified ones
        if len(verified_proxies) < 10:
            print("[yellow]Adding fallback proxies...[/yellow]")
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                fallback_futures: Dict[Future, ProxyString] = {executor.submit(self._check_proxy, proxy): proxy for proxy in fallback_proxies if proxy not in verified_proxies}
                for future in fallback_futures:
                    proxy = fallback_futures[future]
                    if future.result():
                        verified_proxies.append(proxy)
                        print(f"[green]Added fallback proxy: {proxy}[/green]")

        return verified_proxies

    def _check_proxy(self, proxy: ProxyString) -> bool:
        test_urls: List[str] = [
            'http://www.httpbin.org/ip',
            'https://api.ipify.org',
            'http://ip-api.com/json/',
            'https://www.google.com',
        ]

        try:
            test_url: str = random.choice(test_urls)
            response: Response = requests.get(
                test_url,
                proxies={'http': proxy, 'https': proxy},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_next_proxy(self) -> ProxyString:
        try:
            proxy: ProxyString = next(self.proxy_cycle)
            if not isinstance(proxy, str):
                proxy = str(proxy)
            proxy = proxy.strip()
            if not proxy.startswith(('http://', 'https://')):
                proxy = f'http://{proxy}'
            return proxy
        except StopIteration:
            # If we run out of proxies, refresh and try again
            self.refresh_proxies()
            return self.get_next_proxy()

    def refresh_proxies(self) -> None:
        print("[yellow]Refreshing proxies...[/yellow]")
        new_proxies: List[ProxyString] = self._load_proxies()
        
        # Keep track of removed and added proxies
        removed_proxies: Set[ProxyString] = set(self.proxies) - set(new_proxies)
        added_proxies: Set[ProxyString] = set(new_proxies) - set(self.proxies)
        
        self.proxies = new_proxies
        self.proxy_cycle = cycle(self.proxies)
        
        print(f"[bold green]Found {len(self.proxies)} working proxies after refresh[/bold green]")
        print(f"[yellow]Removed {len(removed_proxies)} proxies[/yellow]")
        print(f"[green]Added {len(added_proxies)} new proxies[/green]")

    def _auto_refresh(self) -> None:
        self.refresh_proxies()
        if self.auto_refresh and self.refresh_timer is not None:
            self.refresh_timer = threading.Timer(self.refresh_interval, self._auto_refresh)
            self.refresh_timer.start()

    def stop_auto_refresh(self) -> None:
        if self.auto_refresh and self.refresh_timer is not None:
            self.refresh_timer.cancel()
            self.auto_refresh = False

    def start_auto_refresh(self) -> None:
        if not self.auto_refresh:
            self.auto_refresh = True
            self._auto_refresh()

    def get_proxy_count(self) -> int:
        return len(self.proxies)

    def get_all_proxies(self) -> List[ProxyString]:
        return self.proxies.copy()


# Usage example
if __name__ == "__main__":
    proxy_manager = ProxyManager(max_proxies_per_source=20, auto_refresh=False, refresh_interval=300, max_threads=100)  # Auto-refresh every 5 minutes
    
    # Get a proxy
    proxy = proxy_manager.get_next_proxy()
    print(f"Using proxy: {proxy}")

    # Get proxy count
    print(f"Total proxies: {proxy_manager.get_proxy_count()}")

    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("Stopping proxy manager...")
    #     proxy_manager.stop_auto_refresh()
    #     proxy_manager.save_proxy_stats()

