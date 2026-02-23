"""Tests for the CLI interface."""

from click.testing import CliRunner

from ventureoracle.cli import cli


def test_cli_help():
    """CLI should show help text."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "VentureOracle" in result.output


def test_dashboard_empty():
    """Dashboard should work with no data."""
    runner = CliRunner()
    result = runner.invoke(cli, ["dashboard"])
    assert result.exit_code == 0
    assert "Dashboard" in result.output


def test_profile_show_empty():
    """Profile show should handle no profile gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "show"])
    assert result.exit_code == 0
    assert "No profile" in result.output


def test_predict_list_empty():
    """Predict list should handle no predictions gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "list"])
    assert result.exit_code == 0
    assert "No predictions" in result.output


def test_ingest_file(tmp_path):
    """Should ingest a local file."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test Post\n\nThis is a test post about AI and startups.")

    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", "file", str(md_file)])
    assert result.exit_code == 0
    assert "Ingested" in result.output
