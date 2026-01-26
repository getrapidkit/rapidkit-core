from importlib import import_module


def test_generator_entrypoint() -> None:
    module = import_module("modules.free.essentials.deployment.generate")
    assert hasattr(module, "main")  # nosec B101 - test assertion
