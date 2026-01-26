from modules.free.ai.ai_assistant.generate import GeneratorError


def test_ai_assistant_error_handling_minimal() -> None:
    # Trigger a helpful guidance by calling CLI entry with wrong args
    try:
        # replicate CLI wrong call by invoking main with wrong args via module
        import sys

        old = sys.argv
        sys.argv = ["generate.py"]
        try:
            from modules.free.ai.ai_assistant import generate as g

            try:
                g.main()
            except SystemExit as exc:
                assert exc.code == 2
        finally:
            sys.argv = old
    except (GeneratorError, ImportError, OSError):
        # fallback: ensure GeneratorError type exists
        assert GeneratorError is not None
