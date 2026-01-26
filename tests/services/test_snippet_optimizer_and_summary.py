from pathlib import Path

from core.services import snippet_optimizer as so, summary as summ


def test_remove_inject_markers(tmp_path: Path):
    proj = tmp_path / "proj"
    proj.mkdir()
    a = proj / "a.py"
    b = proj / "b.py"
    bad = proj / "bad.py"
    # a has a standalone marker line
    a.write_text("# <<<inject:foo>>>\nprint('hi')\n")
    # b has inline marker
    b.write_text("x = 1 # <<<inject:foo>>>\n")
    # bad file encoded bytes to cause UnicodeDecodeError on read_text
    bad.write_bytes(b"\xff\xff\xff")

    modified, skipped = so.remove_inject_markers(proj, dry_run=True)
    mods = {p.name for p in modified}
    skips = {p.name for p in skipped}
    assert "a.py" in mods and "b.py" in mods
    assert "bad.py" in skips

    # now actually write changes
    modified2, skipped2 = so.remove_inject_markers(proj, dry_run=False)
    assert (b.read_text()).startswith("x = 1")
    assert (a.read_text()).startswith("print('hi')")


def test_build_minimal_config_summary():
    cfg = {"name": "n", "display_name": "d", "version": "v", "root_path": "/r"}
    out = summ.build_minimal_config_summary(cfg, "p")
    assert "Features: -" in out
    assert "Files: -" in out

    cfg2 = {
        "name": "n2",
        "display_name": "D2",
        "version": "v2",
        "root_path": "/r2",
        "features": {"feat1": {"profiles": ["p"]}},
        "features_files": {"feat1": [{"path": f"f{i}"} for i in range(7)]},
        "depends_on": {"p": [{"name": "dep1"}]},
    }
    out2 = summ.build_minimal_config_summary(cfg2, "p")
    assert "+1 more" in out2
    assert "dep1" in out2
