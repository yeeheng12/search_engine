# test_main.py - Integration tests for the CLI command loop

import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import main


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def run_commands(commands):
    """
    Simulate the CLI loop with a list of commands.
    Returns printed output as a string.
    """
    inputs = iter(commands)
    with patch('builtins.input', side_effect=inputs):
        with patch('sys.stdout') as mock_stdout:
            try:
                main.main()
            except StopIteration:
                pass
    return mock_stdout


# ------------------------------------------------------------------
# CLI command tests
# ------------------------------------------------------------------

class TestMainCLI:

    @patch('main.Search')
    @patch('main.Indexer')
    def test_load_success(self, mock_indexer_class, mock_search_class, capsys):
        mock_indexer = MagicMock()
        mock_indexer.load.return_value = True
        mock_indexer.index = {}
        mock_indexer.documents = {}
        mock_indexer_class.return_value = mock_indexer

        with patch('builtins.input', side_effect=['load', 'quit']):
            main.main()

        mock_indexer.load.assert_called_once()

    @patch('main.Indexer')
    def test_load_missing_file(self, mock_indexer_class, capsys):
        mock_indexer = MagicMock()
        mock_indexer.load.return_value = False
        mock_indexer_class.return_value = mock_indexer

        with patch('builtins.input', side_effect=['load', 'quit']):
            main.main()

        captured = capsys.readouterr()
        assert "build" in captured.out.lower() or "not found" in captured.out.lower()

    @patch('main.Indexer')
    def test_print_without_load(self, mock_indexer_class, capsys):
        mock_indexer_class.return_value = MagicMock()

        with patch('builtins.input', side_effect=['print nonsense', 'quit']):
            main.main()

        captured = capsys.readouterr()
        assert "load" in captured.out.lower() or "index" in captured.out.lower()

    @patch('main.Indexer')
    def test_find_without_load(self, mock_indexer_class, capsys):
        mock_indexer_class.return_value = MagicMock()

        with patch('builtins.input', side_effect=['find good friends', 'quit']):
            main.main()

        captured = capsys.readouterr()
        assert "load" in captured.out.lower() or "index" in captured.out.lower()

    @patch('main.Indexer')
    def test_unknown_command(self, mock_indexer_class, capsys):
        mock_indexer_class.return_value = MagicMock()

        with patch('builtins.input', side_effect=['unknowncommand', 'quit']):
            main.main()

        captured = capsys.readouterr()
        assert "unknown" in captured.out.lower()

    @patch('main.Indexer')
    def test_empty_input_ignored(self, mock_indexer_class, capsys):
        mock_indexer_class.return_value = MagicMock()

        with patch('builtins.input', side_effect=['', 'quit']):
            main.main()

        captured = capsys.readouterr()
        assert "Search Engine" in captured.out

    @patch('main.Indexer')
    def test_help_command(self, mock_indexer_class, capsys):
        mock_indexer_class.return_value = MagicMock()

        with patch('builtins.input', side_effect=['help', 'quit']):
            main.main()

        captured = capsys.readouterr()
        assert "build" in captured.out
        assert "load" in captured.out
        assert "find" in captured.out

    @patch('main.Indexer')
    def test_print_missing_argument(self, mock_indexer_class, capsys):
        mock_indexer = MagicMock()
        mock_indexer.load.return_value = True
        mock_indexer.index = {'good': {}}
        mock_indexer.documents = {}
        mock_indexer_class.return_value = mock_indexer

        with patch('builtins.input', side_effect=['load', 'print', 'quit']):
            main.main()

        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or "load" in captured.out.lower()

    @patch('main.Indexer')
    def test_find_missing_argument(self, mock_indexer_class, capsys):
        mock_indexer = MagicMock()
        mock_indexer.load.return_value = True
        mock_indexer.index = {}
        mock_indexer.documents = {}
        mock_indexer_class.return_value = mock_indexer

        with patch('builtins.input', side_effect=['load', 'find', 'quit']):
            main.main()

        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or "load" in captured.out.lower()

    @patch('main.Search')
    @patch('main.Indexer')
    def test_build_failure_handled(self, mock_indexer_class, mock_search_class, capsys):
        mock_indexer = MagicMock()
        mock_indexer_class.return_value = mock_indexer

        with patch('main.Crawler') as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler.crawl.side_effect = Exception("Network error")
            mock_crawler_class.return_value = mock_crawler

            with patch('builtins.input', side_effect=['build', 'quit']):
                main.main()

        captured = capsys.readouterr()
        assert "failed" in captured.out.lower() or "error" in captured.out.lower()