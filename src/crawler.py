# crawler.py - Crawls quotes.toscrape.com using BFS with a politeness delay

import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class Crawler:
    """
    BFS web crawler for quotes.toscrape.com.

    Design decisions:
    - BFS queue mirrors the lecture's frontier model for graph traversal
    - visited set prevents duplicate crawling
    - 6-second politeness delay required by the coursework brief
    - Same-domain filtering prevents crawling external sites
    - Custom User-Agent identifies the crawler politely
    - Timeout on requests prevents hanging on slow responses
    """

    HEADERS = {
        'User-Agent': 'COMP3011-SearchEngine-Crawler/1.0 (University coursework)'
    }

    def __init__(self, base_url, politeness=6):
        """
        Args:
            base_url (str): the starting URL to crawl from
            politeness (int): seconds to wait between requests (minimum 6)
        """
        self.base_url = base_url.rstrip('/')
        self.politeness = max(politeness, 6)  # enforce minimum 6 seconds
        self.visited = set()
        self.pages = {}
        self.errors = {}

    def crawl(self):
        """
        Crawl the website using BFS starting from base_url.
        Respects politeness delay between every request.

        Returns:
            dict: {url (str): html (str)} for all successfully crawled pages
        """
        # Reset state for a fresh crawl
        self.visited = set()
        self.pages = {}
        self.errors = {}

        queue = [self.base_url + '/']

        while queue:
            url = queue.pop(0)  # BFS: take from front of queue

            if url in self.visited:
                continue

            print(f"  Crawling: {url}")

            try:
                response = requests.get(
                    url,
                    headers=self.HEADERS,
                    timeout=10
                )
                response.raise_for_status()  # raises on 4xx/5xx

                self.visited.add(url)
                self.pages[url] = response.text

                # Extract and queue internal links from this page
                new_links = self._extract_links(response.text, url)
                for link in new_links:
                    if link not in self.visited and link not in queue:
                        queue.append(link)

            except requests.exceptions.Timeout:
                print(f"  Timeout: {url} — skipping")
                self.errors[url] = "timeout"
                self.visited.add(url)  # mark visited to avoid retry

            except requests.exceptions.HTTPError as e:
                print(f"  HTTP error {e.response.status_code}: {url} — skipping")
                self.errors[url] = f"http_{e.response.status_code}"
                self.visited.add(url)

            except requests.exceptions.RequestException as e:
                print(f"  Request failed: {url} — {e}")
                self.errors[url] = str(e)
                self.visited.add(url)

            # Politeness delay after every request attempt
            if queue:
                time.sleep(self.politeness)

        print(f"\nCrawl complete: {len(self.pages)} pages, {len(self.errors)} errors")
        return self.pages

    def _extract_links(self, html, current_url):
        """
        Extract all internal links from an HTML page.
        Converts relative URLs to absolute and filters to same domain only.

        Args:
            html (str): raw HTML content
            current_url (str): the URL this HTML was fetched from

        Returns:
            list[str]: list of absolute internal URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for tag in soup.find_all('a', href=True):
            href = tag['href'].strip()

            # Skip empty, anchor-only, javascript, and mailto links
            if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue

            # Convert relative URL to absolute
            full_url = urljoin(current_url, href)

            # Normalise trailing slash for consistency
            full_url = full_url.rstrip('/') + '/'

            # Only keep internal links on the same domain
            if self._is_internal(full_url) and self._is_allowed(full_url):
                links.append(full_url)

        return links

    def _is_internal(self, url):
        """
        Check if a URL belongs to the same domain as base_url.

        Args:
            url (str): URL to check

        Returns:
            bool: True if same domain
        """
        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc
        return url_domain == base_domain

    def _is_allowed(self, url):
        """
        Filter out URLs that are not useful for indexing.
        Excludes login pages and other non-content pages.

        Args:
            url (str): URL to check

        Returns:
            bool: True if the URL should be crawled
        """
        excluded = ['/login', '/logout', '/register']
        path = urlparse(url).path
        return not any(path.startswith(ex) for ex in excluded)
