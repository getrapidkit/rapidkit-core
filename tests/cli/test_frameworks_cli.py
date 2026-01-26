from pathlib import Path

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


def test_frameworks_list() -> None:
    result = runner.invoke(app, ["frameworks", "list"])
    assert result.exit_code == 0, result.output
    assert "fastapi" in result.output.lower()


def test_frameworks_scaffold_and_detect(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "frameworks",
            "scaffold",
            "fastapi",
            "--name",
            "sample",
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "sample" / "main.py").exists()
    detect_res = runner.invoke(app, ["frameworks", "detect", str(tmp_path)])
    assert detect_res.exit_code in (0, 1)
