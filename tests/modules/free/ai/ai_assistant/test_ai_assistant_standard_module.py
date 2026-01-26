from pathlib import Path

from modules.free.ai.ai_assistant import generate


def test_ai_assistant_standard_module_smoke(tmp_path: Path) -> None:
    target = tmp_path / "out"
    target.mkdir()
    # generate vendor + fastapi variant into temp dir
    renderer = generate._create_generator().create_renderer()
    cfg = generate.load_module_config()
    base_context = generate.build_base_context(cfg)
    generate.generate_vendor_files(cfg, target, renderer, base_context)
    generate.generate_variant_files("fastapi", target, renderer, base_context)

    # assert outputs created
    assert (
        target / "src" / "modules" / "free" / "ai" / "ai_assistant" / "ai_assistant.py"
    ).exists()
    assert (
        target
        / "src"
        / "modules"
        / "free"
        / "ai"
        / "ai_assistant"
        / "routers"
        / "ai"
        / "ai_assistant.py"
    ).exists()
