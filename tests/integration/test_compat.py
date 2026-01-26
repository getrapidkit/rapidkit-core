def test_compat_import_and_shims() -> None:
    """Import `cli._compat` and check basic shim presence.

    This ensures the module imports without raising and that the expected
    attributes exist on Click/Typer objects in the runtime environment.
    """
    import importlib

    compat = importlib.import_module("cli._compat")
    assert compat is not None

    # Basic runtime check: if click is available, Parameter should expose make_metavar
    try:
        from click.core import Parameter as _ClickParameter

        assert hasattr(_ClickParameter, "make_metavar")
    except ImportError:
        # click not available in this test environment — still a pass
        pass
