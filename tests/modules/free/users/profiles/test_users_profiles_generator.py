from importlib import import_module


def test_users_profiles_generator_entrypoint() -> None:
    module = import_module("modules.free.users.users_profiles.generate")
    assert module
