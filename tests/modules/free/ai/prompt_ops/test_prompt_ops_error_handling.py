import pytest


def test_prompt_ops_raises_clear_errors(rendered_prompt_ops) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_prompt_ops["vendor"]

    ops = vendor.PromptOps()

    with pytest.raises(vendor.PromptOpsError):
        ops.create_prompt("", "template")
    with pytest.raises(KeyError):
        ops.get_version("missing", 1)
