# test_search.py - Unit tests for print and find search logic

import pytest
import os
import sys
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search import Search


# ------------------------------------------------------------------
# Shared test fixtures
# ------------------------------------------------------------------

MOCK_INDEX = {
    "good": {
        "1": {"frequency": 2, "positions": [0, 5]},
        "2": {"frequency": 1, "positions": [3]}
    },
    "friends": {
        "1": {"frequency": 1, "positions": [3]},
        "3": {"frequency": 2, "positions": [1, 7]}
    },
    "indifference": {
        "3": {"frequency": 1, "positions": [0]}
    },
    "life": {
        "1": {"frequency": 1, "positions": [10]},
        "2": {"frequency": 2, "positions": [4, 9]},
        "3": {"frequency": 1, "positions": [5]}
    }
}

MOCK_DOCUMENTS = {
    "1": {"url": "http://quotes.com/page/1/", "title": "Page 1", "word_count": 50},
    "2": {"url": "http://quotes.com/page/2/", "title": "Page 2", "word_count": 40},
    "3": {"url": "http://quotes.com/page/3/", "title": "Page 3", "word_count": 60}
}


@pytest.fixture
def searcher():
    return Search(MOCK_INDEX, MOCK_DOCUMENTS)


# ------------------------------------------------------------------
# print_word tests
# ------------------------------------------------------------------

class TestPrintWord:

    def test_print_known_word(self, searcher, capsys):
        searcher.print_word("good")
        captured = capsys.readouterr()
        assert "good" in captured.out
        assert "http://quotes.com/page/1/" in captured.out

    def test_print_case_insensitive(self, searcher, capsys):
        searcher.print_word("Good")
        captured = capsys.readouterr()
        assert "good" in captured.out

    def test_print_unknown_word(self, searcher, capsys):
        searcher.print_word("nonsense")
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_print_empty_input(self, searcher, capsys):
        searcher.print_word("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_print_shows_frequency(self, searcher, capsys):
        searcher.print_word("good")
        captured = capsys.readouterr()
        assert "frequency" in captured.out

    def test_print_shows_positions(self, searcher, capsys):
        searcher.print_word("good")
        captured = capsys.readouterr()
        assert "positions" in captured.out


# ------------------------------------------------------------------
# find tests
# ------------------------------------------------------------------

class TestFind:

    def test_find_single_word(self, searcher):
        results = searcher.find("indifference")
        assert "http://quotes.com/page/3/" in results

    def test_find_multi_word_intersection(self, searcher):
        # good appears in doc 1 and 2, friends in doc 1 and 3
        # intersection = doc 1 only
        results = searcher.find("good friends")
        assert "http://quotes.com/page/1/" in results
        assert "http://quotes.com/page/2/" not in results
        assert "http://quotes.com/page/3/" not in results

    def test_find_case_insensitive(self, searcher):
        results = searcher.find("GOOD")
        assert len(results) > 0

    def test_find_missing_word_returns_empty(self, searcher):
        results = searcher.find("nonexistentword")
        assert results == []

    def test_find_empty_query_returns_empty(self, searcher):
        results = searcher.find("")
        assert results == []

    def test_find_whitespace_only_returns_empty(self, searcher):
        results = searcher.find("   ")
        assert results == []

    def test_find_ranking_by_frequency(self, searcher):
        # life appears in all 3 docs
        # doc2 has frequency 2, doc1 and doc3 have frequency 1
        results = searcher.find("life")
        assert results[0] == "http://quotes.com/page/2/"

    def test_find_no_intersection_returns_empty(self, searcher):
        # indifference only in doc3, good not in doc3
        results = searcher.find("good indifference")
        assert results == []

    def test_find_returns_list(self, searcher):
        results = searcher.find("good")
        assert isinstance(results, list)

    def test_find_prints_urls(self, searcher, capsys):
        searcher.find("good")
        captured = capsys.readouterr()
        assert "http://quotes.com" in captured.out