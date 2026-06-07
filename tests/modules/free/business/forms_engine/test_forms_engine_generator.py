from importlib import import_module


def test_forms_engine_generator_entrypoint() -> None:
    """Ensure the module generator can be imported without crashing."""

    generator_module = import_module("modules.free.business.forms_engine.generate")
    assert hasattr(generator_module, "main"), "Expected a main() entrypoint on the generator module"
