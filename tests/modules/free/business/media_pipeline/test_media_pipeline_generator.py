from importlib import import_module


def test_media_pipeline_generator_entrypoint() -> None:
    """Ensure the module generator can be imported without crashing."""

    generator_module = import_module("modules.free.business.media_pipeline.generate")
    assert hasattr(generator_module, "main"), "Expected a main() entrypoint on the generator module"
