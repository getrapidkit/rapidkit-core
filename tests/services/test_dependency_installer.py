from core.engine import dependency_installer as di


def test_caret_to_range_various():
    assert di._caret_to_range("^2.9.0") == ">=2.9.0,<3.0"
    assert di._caret_to_range("^0.30.0") == ">=0.30.0,<0.31.0"
    assert di._caret_to_range("^0.0.3") == ">=0.0.3,<0.0.4"
    # non-caret remains
    assert di._caret_to_range("~=1.2") == "~=1.2"


def test_format_requirements_lines_and_extract_names():
    base = [("alpha", "^1.0.0"), ("zz", "1.2")]
    injected = [("beta", "^0.3.0")]
    base_block, inj_block = di._format_requirements_lines(base, injected)
    assert "alpha" in base_block and "zz" in base_block
    assert "beta" in inj_block
    # extract names
    names = di._extract_requirement_names(base_block + "\n" + inj_block)
    assert "alpha" in names and "beta" in names
