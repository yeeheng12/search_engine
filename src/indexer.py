# indexer.py - Builds an inverted index with frequency and position statistics

import re
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup


class Indexer:
    """
    Builds and stores an inverted index from crawled HTML pages.
    
    Data structures:
        index: {word: {doc_id: {frequency: int, positions: [int]}}}
        documents: {doc_id: {url: str, title: str, word_count: int}}
    
    Design decision: doc IDs are strings for consistent JSON serialisation.
    Design decision: positions are stored to support future phrase matching.
    """

    def __init__(self):
        self.index = {}        # inverted index: word -> doc_id -> stats
        self.documents = {}    # document table: doc_id -> metadata
        self._next_id = 1      # auto-incrementing document ID counter

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def build(self, pages):
        """
        Build the inverted index from a dict of {url: html} pages.
        Resets any previously built index before building.

        Args:
            pages (dict): {url (str): html (str)}

        Returns:
            dict: the completed inverted index
        """
        # Reset state so build can be called fresh each time
        self.index = {}
        self.documents = {}
        self._next_id = 1

        for url, html in pages.items():
            doc_id = str(self._next_id)
            self._next_id += 1

            # Extract and tokenise text from this page
            text = self._extract_text(html)
            tokens = self._tokenise(text)

            # Store document metadata
            title = self._extract_title(html)
            self.documents[doc_id] = {
                "url": url,
                "title": title,
                "word_count": len(tokens)
            }

            # Build postings for this document
            for position, word in enumerate(tokens):
                if word not in self.index:
                    self.index[word] = {}
                if doc_id not in self.index[word]:
                    self.index[word][doc_id] = {
                        "frequency": 0,
                        "positions": []
                    }
                self.index[word][doc_id]["frequency"] += 1
                self.index[word][doc_id]["positions"].append(position)

        return self.index

    def save(self, filepath):
        """
        Save the index, documents, and metadata to a JSON file.

        Args:
            filepath (str): path to save the index file
        """
        # Create directory if it does not exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        payload = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "page_count": len(self.documents),
                "term_count": len(self.index),
                "politeness_delay": 6
            },
            "documents": self.documents,
            "index": self.index
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"Index saved: {len(self.index)} terms, {len(self.documents)} documents -> {filepath}")

    def load(self, filepath):
        """
        Load a previously saved index from a JSON file.

        Args:
            filepath (str): path to the index file

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                payload = json.load(f)

            self.index = payload.get("index", {})
            self.documents = payload.get("documents", {})

            print(f"Index loaded: {len(self.index)} terms, {len(self.documents)} documents")
            return True

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading index: {e}")
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()

        parts = []

        # Targeted extraction for quotes.toscrape.com
        for quote in soup.select('.text'):
            parts.append(quote.get_text())
        for author in soup.select('.author'):
            parts.append(author.get_text())
        for tag in soup.select('.tag'):
            parts.append(tag.get_text())
        if soup.title:
            parts.append(soup.title.get_text())

        # Always also include full body text to capture all page content
        body = soup.get_text(separator=' ')
        parts.append(body)

        return ' '.join(parts)

    def _extract_title(self, html):
        """
        Extract the page title from HTML.

        Args:
            html (str): raw HTML string

        Returns:
            str: page title or empty string
        """
        soup = BeautifulSoup(html, 'html.parser')
        if soup.title:
            return soup.title.get_text().strip()
        return ""

    def _tokenise(self, text):
        """
        Tokenise text into lowercase alphanumeric words.
        Uses the same logic for both indexing and query processing
        to ensure consistent matching.

        Design decisions:
        - Lowercase: required for case-insensitive search
        - Alphanumeric only: avoids punctuation noise
        - No stopword removal: preserves common word queries
        - No stemming: simpler, more predictable results
        - Keeps numbers: meaningful in some contexts

        Args:
            text (str): plain text string

        Returns:
            list[str]: list of lowercase tokens
        """
        if not text:
            return []
        return re.findall(r'[a-z0-9]+', text.lower())