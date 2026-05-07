# test_crawler.py - Unit tests for crawler using mocked HTTP responses

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crawler import Crawler


# ------------------------------------------------------------------
# Shared HTML fixtures
# ------------------------------------------------------------------

SIMPLE_HTML = """
<html>
<body>
    <a href="/page/2/">Page 2</a>
    <a href="/page/3/">Page 3</a>
    <a href="https://external.com/">External</a>
</body>
</html>
"""

PAGE_2_HTML = """
<html><body><p>Page 2 content</p></body></html>
"""


def make_mock_response(html, status_code=200):
    """Helper to create a mock requests.Response object."""
    mock = MagicMock()
    mock.text = html
    mock.status_code = status_code
    mock.raise_for_status = MagicMock()
    return mock


# ------------------------------------------------------------------
# Initialisation tests
# ------------------------------------------------------------------

class TestCrawlerInit:

    def test_default_politeness_minimum(self):
        # Should enforce minimum 6 seconds even if less is passed
        crawler = Crawler('https://quotes.toscrape.com', politeness=1)
        assert crawler.politeness >= 6

    def test_base_url_stored(self):
        crawler = Crawler('https://quotes.toscrape.com')
        assert 'quotes.toscrape.com' in crawler.base_url


# ------------------------------------------------------------------
# Link extraction tests
# ------------------------------------------------------------------

class TestExtractLinks:

    def setup_method(self):
        self.crawler = Crawler('https://quotes.toscrape.com')

    def test_extracts_internal_links(self):
        links = self.crawler._extract_links(SIMPLE_HTML, 'https://quotes.toscrape.com/')
        assert any('page/2' in l for l in links)
        assert any('page/3' in l for l in links)

    def test_excludes_external_links(self):
        links = self.crawler._extract_links(SIMPLE_HTML, 'https://quotes.toscrape.com/')
        assert not any('external.com' in l for l in links)

    def test_excludes_login_page(self):
        html = '<html><body><a href="/login/">Login</a></body></html>'
        links = self.crawler._extract_links(html, 'https://quotes.toscrape.com/')
        assert not any('login' in l for l in links)

    def test_relative_urls_converted(self):
        html = '<html><body><a href="/page/2/">link</a></body></html>'
        links = self.crawler._extract_links(html, 'https://quotes.toscrape.com/')
        assert any(l.startswith('https://') for l in links)

    def test_empty_html_returns_empty(self):
        links = self.crawler._extract_links('<html></html>', 'https://quotes.toscrape.com/')
        assert links == []

    def test_anchor_only_links_excluded(self):
        html = '<html><body><a href="#">top</a></body></html>'
        links = self.crawler._extract_links(html, 'https://quotes.toscrape.com/')
        assert links == []


# ------------------------------------------------------------------
# Domain filtering tests
# ------------------------------------------------------------------

class TestIsInternal:

    def setup_method(self):
        self.crawler = Crawler('https://quotes.toscrape.com')

    def test_same_domain_is_internal(self):
        assert self.crawler._is_internal('https://quotes.toscrape.com/page/2/') is True

    def test_different_domain_is_external(self):
        assert self.crawler._is_internal('https://google.com') is False

    def test_subdomain_is_external(self):
        assert self.crawler._is_internal('https://sub.quotes.toscrape.com') is False


# ------------------------------------------------------------------
# Crawl behaviour tests (mocked HTTP)
# ------------------------------------------------------------------

class TestCrawl:

    @patch('crawler.time.sleep')
    @patch('crawler.requests.get')
    def test_crawl_returns_pages_dict(self, mock_get, mock_sleep):
        mock_get.return_value = make_mock_response(SIMPLE_HTML)
        crawler = Crawler('https://quotes.toscrape.com', politeness=6)
        pages = crawler.crawl()
        assert isinstance(pages, dict)
        assert len(pages) > 0

    @patch('crawler.time.sleep')
    @patch('crawler.requests.get')
    def test_politeness_delay_called(self, mock_get, mock_sleep):
        # Give the first page a link so the crawler queues a second page
        # This means the queue is non-empty after the first request, triggering sleep
        html_with_link = '<html><body><a href="/page/2/">Page 2</a></body></html>'
        mock_get.return_value = make_mock_response(html_with_link)
        crawler = Crawler('https://quotes.toscrape.com', politeness=6)
        crawler.crawl()
        mock_sleep.assert_called_with(6)

    @patch('crawler.time.sleep')
    @patch('crawler.requests.get')
    def test_does_not_revisit_urls(self, mock_get, mock_sleep):
        mock_get.return_value = make_mock_response(SIMPLE_HTML)
        crawler = Crawler('https://quotes.toscrape.com', politeness=6)
        crawler.crawl()
        # Each URL should appear only once in visited
        assert len(crawler.visited) == len(set(crawler.visited))

    @patch('crawler.time.sleep')
    @patch('crawler.requests.get')
    def test_handles_timeout_gracefully(self, mock_get, mock_sleep):
        import requests as req
        mock_get.side_effect = req.exceptions.Timeout
        crawler = Crawler('https://quotes.toscrape.com', politeness=6)
        pages = crawler.crawl()
        # Should not crash, just return empty pages
        assert isinstance(pages, dict)
        assert 'https://quotes.toscrape.com/' in crawler.errors

    @patch('crawler.time.sleep')
    @patch('crawler.requests.get')
    def test_handles_http_error_gracefully(self, mock_get, mock_sleep):
        import requests as req
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = req.exceptions.HTTPError(
            response=mock_response
        )
        crawler = Crawler('https://quotes.toscrape.com', politeness=6)
        pages = crawler.crawl()
        assert isinstance(pages, dict)

    @patch('crawler.time.sleep')
    @patch('crawler.requests.get')
    def test_custom_user_agent_sent(self, mock_get, mock_sleep):
        mock_get.return_value = make_mock_response('<html><body></body></html>')
        crawler = Crawler('https://quotes.toscrape.com', politeness=6)
        crawler.crawl()
        call_kwargs = mock_get.call_args
        assert 'headers' in call_kwargs.kwargs or 'headers' in str(call_kwargs)