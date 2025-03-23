"""Tests for the Prowlpy __init__.py."""

from unittest.mock import patch


def test_main_import():
    """Test CLI import."""
    with patch("prowlpy._cli.main") as mock_main:
        from prowlpy._cli import main  # noqa: PLC0415, PLC2701

        assert callable(main)
        main()
        mock_main.assert_called_once()


def test_main_import_fallback():
    """Test CLI not available."""
    with patch.dict("sys.modules", {"prowlpy._cli": None}):
        from prowlpy.__init__ import main  # noqa: PLC0415, PLC2701

        assert callable(main)
    with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
        main()
        mock_print.assert_called_once_with(
            "The Prowlpy command line client could not be run because the required dependencies were not installed.\n"
            "Make sure it is installed with pip install prowlpy[cli]",
        )
        mock_exit.assert_called_once_with(1)
