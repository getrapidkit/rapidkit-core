from modules.free.ai.ai_assistant import generate


def test_ai_assistant_adapters_basic() -> None:
    """Ai Assistant: generator exposes adapter points and generation functions."""
    assert hasattr(generate, "generate_variant_files")
    assert hasattr(generate, "generate_vendor_files")
