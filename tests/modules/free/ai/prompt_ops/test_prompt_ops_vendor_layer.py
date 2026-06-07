def test_prompt_ops_vendor_exports_contract(rendered_prompt_ops) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_prompt_ops["vendor"]

    for name in (
        "PromptOps",
        "PromptOpsConfig",
        "PromptOpsError",
        "PromptStatus",
        "PromptVersion",
        "PromptEvaluation",
    ):
        assert hasattr(vendor, name)
