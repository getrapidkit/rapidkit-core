from importlib import import_module


def test_org_admin_console_generator_entrypoint() -> None:
    """Ensure the module generator can be imported without crashing."""

    generator_module = import_module("modules.free.business.org_admin_console.generate")
    assert hasattr(generator_module, "main"), "Expected a main() entrypoint on the generator module"
