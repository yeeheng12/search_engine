# main.py - CLI command loop for the search engine

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from indexer import Indexer
from search import Search
from crawler import Crawler

INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'index.json')
BASE_URL = 'https://quotes.toscrape.com/'

HELP_TEXT = """
Available commands:
  build        - Crawl the website and build the index
  load         - Load a previously built index
  print <word> - Print the posting list for a word
  find <query> - Find pages containing all query terms
  help         - Show this help message
  quit         - Exit the search engine
"""


def main():
    """
    Main CLI loop for the search engine.
    Coordinates build, load, print, and find commands.
    Does not contain crawler/indexer/search logic itself.
    """
    indexer = Indexer()
    searcher = None

    print("=" * 50)
    print(" Search Engine - COMP3011 Coursework 2")
    print("=" * 50)
    print(HELP_TEXT)

    while True:
        try:
            raw = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        # Split into command and optional arguments
        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ''

        # -------------------------------------------------------
        if command == 'build':
            print("\nStarting crawl of", BASE_URL)
            print("This will take several minutes due to the 6-second politeness window.")
            print("Please wait...\n")

            try:
                crawler = Crawler(BASE_URL, politeness=6)
                pages = crawler.crawl()

                if not pages:
                    print("Crawl returned no pages. Check your connection.")
                    continue

                print(f"Crawled {len(pages)} pages. Building index...")
                indexer.build(pages)
                indexer.save(INDEX_PATH)
                searcher = Search(indexer.index, indexer.documents)
                print("Build complete. You can now use print and find.\n")

            except Exception as e:
                print(f"Build failed: {e}\n")

        # -------------------------------------------------------
        elif command == 'load':
            success = indexer.load(INDEX_PATH)
            if success:
                searcher = Search(indexer.index, indexer.documents)
                print("Ready. You can now use print and find.\n")
            else:
                print("Index file not found. Run 'build' first.\n")

        # -------------------------------------------------------
        elif command == 'print':
            if searcher is None:
                print("No index loaded. Run 'build' or 'load' first.\n")
            elif not args:
                print("Usage: print <word>\n")
            else:
                searcher.print_word(args)

        # -------------------------------------------------------
        elif command == 'find':
            if searcher is None:
                print("No index loaded. Run 'build' or 'load' first.\n")
            elif not args:
                print("Usage: find <query terms>\n")
            else:
                searcher.find(args)

        # -------------------------------------------------------
        elif command == 'help':
            print(HELP_TEXT)

        elif command == 'quit' or command == 'exit':
            print("Exiting.")
            break

        else:
            print(f"Unknown command: '{command}'. Type 'help' for available commands.\n")


if __name__ == '__main__':
    main()