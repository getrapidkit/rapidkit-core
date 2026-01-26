from importlib import import_module


def test_users_core_generator_entrypoint() -> None:
    module = import_module("modules.free.users.users_core.generate")
    assert module
