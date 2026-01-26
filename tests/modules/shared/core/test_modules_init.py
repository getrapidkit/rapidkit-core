# tests/test_modules_init.py
"""Test the modules package initialization."""


def test_modules_all_attribute():
    """Test that __all__ is defined in modules package."""
    from modules import __all__

    # Should be a list (even if empty)
    assert isinstance(__all__, list)
    # Currently empty, but test structure is in place
    assert len(__all__) == 0
