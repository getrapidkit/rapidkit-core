from core.engine import dependency_installer as di


def test_align_requirements_base_block_simple():
    before = "alpha==1.0\nbeta>=2.0\n# comment\n"
    out = di._align_requirements_base_block(before, ["gamma"])
    assert "alpha" in out and "beta" in out
