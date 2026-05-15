"""Tests for main CLI app."""

from typer.testing import CliRunner

from asantico_cli import __version__
from asantico_cli.cli.app import app

runner = CliRunner()


class TestMainApp:
    """Tests for the main CLI application."""

    def test_help_flag(self) -> None:
        """--help shows help text and exits successfully."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Generate professional PDF invoices" in result.stdout
        assert "invoice" in result.stdout
        assert "estimate" in result.stdout
        assert "properties" in result.stdout
        assert "rates" in result.stdout

    def test_version_flag(self) -> None:
        """--version shows version number and exits successfully."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert f"asantico, version {__version__}" in result.stdout

    def test_no_args_shows_help(self) -> None:
        """Running with no arguments shows help."""
        result = runner.invoke(app, [])

        # no_args_is_help=True causes Typer to show help
        # Exit code may be 0 or 2 depending on Typer version
        assert "invoice" in result.stdout or "invoice" in str(result.output)
