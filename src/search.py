# search.py - Handles print and find queries against the inverted index

import re

class Search:
    """
    Handles search queries against a loaded inverted index.

    Supports:
        - print: show posting list for a single word
        - find: conjunctive multi-word search with frequency-based ranking

    Design decision: conjunctive search means ALL query terms must appear
    in a page for it to be returned. This matches the coursework example
    where 'find good friends' returns pages containing both words.
    """

    def __init__(self, index, documents):
        """
        Args:
            index (dict): inverted index {word: {doc_id: {frequency, positions}}}
            documents (dict): document table {doc_id: {url, title, word_count}}
        """
        self.index = index
        self.documents = documents

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def print_word(self, word):
        """
        Print the posting list for a single word.
        Shows each page URL, frequency, and positions.

        Args:
            word (str): the word to look up (case-insensitive)
        """
        if not word or not word.strip():
            print("Usage: print <word>")
            return

        # Use same tokeniser logic — lowercase, strip punctuation
        word = self._normalise(word)

        if not word:
            print("Usage: print <word>")
            return

        if word not in self.index:
            print(f"'{word}' not found in index.")
            return

        postings = self.index[word]
        print(f"\nPosting list for '{word}' ({len(postings)} document(s)):\n")

        for doc_id, stats in postings.items():
            url = self._get_url(doc_id)
            freq = stats["frequency"]
            positions = stats["positions"]
            print(f"  [{doc_id}] {url}")
            print(f"       frequency : {freq}")
            print(f"       positions : {positions}\n")

    def find(self, query):
        """
        Find pages containing ALL query terms (conjunctive search).
        Results are ranked by total frequency of query terms in each page.

        Args:
            query (str): one or more search terms

        Returns:
            list[str]: list of matching URLs sorted by score descending
        """
        if not query or not query.strip():
            print("Usage: find <query terms>")
            return []

        # Tokenise query using same logic as indexer
        words = self._tokenise(query)

        if not words:
            print("Usage: find <query terms>")
            return []

        # Check every query term exists in the index
        missing = [w for w in words if w not in self.index]
        if missing:
            for w in missing:
                print(f"'{w}' not found in index.")
            return []

        # Conjunctive intersection — pages must contain ALL words
        result_sets = [set(self.index[w].keys()) for w in words]
        common_doc_ids = result_sets[0].intersection(*result_sets[1:])

        if not common_doc_ids:
            print("No pages found containing all query terms.")
            return []

        # Score each matching page by total frequency of all query words
        scored = []
        for doc_id in common_doc_ids:
            score = sum(
                self.index[w][doc_id]["frequency"]
                for w in words
            )
            url = self._get_url(doc_id)
            scored.append((score, doc_id, url))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        print(f"\nFound {len(scored)} page(s) for '{' '.join(words)}':\n")
        for score, doc_id, url in scored:
            print(f"  [score: {score}] {url}")

        print()
        return [url for _, _, url in scored]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalise(self, word):
        """
        Normalise a single word using the same rules as the indexer.
        Extracts the first alphanumeric token only.

        Args:
            word (str): raw input word

        Returns:
            str: normalised word or empty string
        """
        tokens = re.findall(r'[a-z0-9]+', word.lower())
        return tokens[0] if tokens else ""

    def _tokenise(self, text):
        """
        Tokenise a query string into lowercase alphanumeric words.
        Must match the tokeniser used in indexer.py exactly.

        Args:
            text (str): raw query string

        Returns:
            list[str]: list of lowercase tokens
        """
        if not text:
            return []
        return re.findall(r'[a-z0-9]+', text.lower())

    def _get_url(self, doc_id):
        """
        Look up a URL from the document table by doc ID.

        Args:
            doc_id (str): document identifier

        Returns:
            str: URL or fallback string if not found
        """
        doc = self.documents.get(doc_id, {})
        return doc.get("url", f"[unknown doc {doc_id}]")