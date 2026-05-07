# test_indexer.py - Unit tests for tokeniser, index builder, and storage

import pytest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from indexer import Indexer
from search import Search


# ------------------------------------------------------------------
# Tokeniser tests
# ------------------------------------------------------------------

class TestTokenise:

    def setup_method(self):
        self.indexer = Indexer()

    def test_lowercase_conversion(self):
        tokens = self.indexer._tokenise("Hello World")
        assert tokens == ["hello", "world"]

    def test_punctuation_removed(self):
        tokens = self.indexer._tokenise("good, friends.")
        assert "good" in tokens
        assert "friends" in tokens

    def test_empty_string(self):
        tokens = self.indexer._tokenise("")
        assert tokens == []

    def test_none_like_empty(self):
        tokens = self.indexer._tokenise("")
        assert tokens == []

    def test_numbers_kept(self):
        tokens = self.indexer._tokenise("page 2")
        assert "2" in tokens

    def test_mixed_case(self):
        tokens = self.indexer._tokenise("Good GOOD good")
        assert tokens.count("good") == 3

    def test_apostrophe_handling(self):
        # apostrophes should be stripped cleanly
        tokens = self.indexer._tokenise("it's")
        assert "it" in tokens or "its" in tokens  # either is acceptable


# ------------------------------------------------------------------
# Index builder tests
# ------------------------------------------------------------------

class TestBuildIndex:

    def setup_method(self):
        self.indexer = Indexer()

    def test_basic_frequency_count(self):
        pages = {"http://test.com": "<html><body>hello world hello</body></html>"}
        index = self.indexer.build(pages)
        doc_id = list(index["hello"].keys())[0]
        assert index["hello"][doc_id]["frequency"] == 2

    def test_position_recorded(self):
        pages = {"http://test.com": "<html><body>apple banana apple</body></html>"}
        index = self.indexer.build(pages)
        doc_id = list(index["apple"].keys())[0]
        assert len(index["apple"][doc_id]["positions"]) == 2

    def test_case_insensitive_indexing(self):
        pages = {"http://test.com": "<html><body>Good GOOD good</body></html>"}
        index = self.indexer.build(pages)
        doc_id = list(index["good"].keys())[0]
        assert index["good"][doc_id]["frequency"] == 3

    def test_multiple_pages(self):
        pages = {
            "http://test.com/1": "<html><body>hello world</body></html>",
            "http://test.com/2": "<html><body>hello python</body></html>"
        }
        index = self.indexer.build(pages)
        assert len(index["hello"]) == 2

    def test_document_table_populated(self):
        pages = {"http://test.com": "<html><title>Test</title><body>hello</body></html>"}
        self.indexer.build(pages)
        assert len(self.indexer.documents) == 1
        doc = list(self.indexer.documents.values())[0]
        assert doc["url"] == "http://test.com"

    def test_word_count_in_document(self):
        pages = {"http://test.com": "<html><body>one two three</body></html>"}
        self.indexer.build(pages)
        doc = list(self.indexer.documents.values())[0]
        assert doc["word_count"] == 3

    def test_empty_page(self):
        pages = {"http://test.com": "<html><body></body></html>"}
        index = self.indexer.build(pages)
        assert isinstance(index, dict)

    def test_build_resets_previous_index(self):
        pages1 = {"http://test.com": "<html><body>hello</body></html>"}
        pages2 = {"http://other.com": "<html><body>world</body></html>"}
        self.indexer.build(pages1)
        self.indexer.build(pages2)
        # hello should not appear after second build
        assert "hello" not in self.indexer.index


# ------------------------------------------------------------------
# Save and load tests
# ------------------------------------------------------------------

class TestSaveLoad:

    def setup_method(self):
        self.indexer = Indexer()
        self.test_path = "data/test_index.json"

    def teardown_method(self):
        # Clean up test file after each test
        if os.path.exists(self.test_path):
            os.remove(self.test_path)

    def test_save_creates_file(self):
        pages = {"http://test.com": "<html><body>hello</body></html>"}
        self.indexer.build(pages)
        self.indexer.save(self.test_path)
        assert os.path.exists(self.test_path)

    def test_save_and_load_roundtrip(self):
        pages = {"http://test.com": "<html><body>hello world</body></html>"}
        self.indexer.build(pages)
        self.indexer.save(self.test_path)

        new_indexer = Indexer()
        result = new_indexer.load(self.test_path)
        assert result is True
        assert "hello" in new_indexer.index

    def test_load_missing_file_returns_false(self):
        result = self.indexer.load("data/nonexistent.json")
        assert result is False

    def test_saved_file_contains_metadata(self):
        pages = {"http://test.com": "<html><body>hello</body></html>"}
        self.indexer.build(pages)
        self.indexer.save(self.test_path)

        with open(self.test_path, 'r') as f:
            data = json.load(f)

        assert "metadata" in data
        assert "documents" in data
        assert "index" in data

# ------------------------------------------------------------------
# Performance tests
# ------------------------------------------------------------------

import time

class TestPerformance:

    def test_build_speed_large_input(self):
        """Index build should complete within 2 seconds for 100 pages."""
        indexer = Indexer()
        pages = {
            f"http://test.com/page/{i}": f"<html><body>{'word ' * 200} unique{i}</body></html>"
            for i in range(100)
        }
        start = time.time()
        indexer.build(pages)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Build too slow: {elapsed:.2f}s"

    def test_search_speed(self):
        """Search across large index should complete within 0.1 seconds."""
        indexer = Indexer()
        pages = {
            f"http://test.com/page/{i}": f"<html><body>good friends life love word{i}</body></html>"
            for i in range(100)
        }
        indexer.build(pages)
        searcher = Search(indexer.index, indexer.documents)

        start = time.time()
        for _ in range(100):
            searcher.find("good friends")
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Search too slow: {elapsed:.2f}s"

    def test_tokeniser_speed(self):
        """Tokeniser should handle large text within 0.1 seconds."""
        indexer = Indexer()
        large_text = "good friends life love " * 10000
        start = time.time()
        tokens = indexer._tokenise(large_text)
        elapsed = time.time() - start
        assert elapsed < 0.1
        assert len(tokens) > 0