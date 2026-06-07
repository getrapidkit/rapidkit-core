def test_forms_engine_generated_runtime_is_usable(rendered_forms_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_forms_engine["vendor"]
    runtime = vendor.FormsEngine()

    assert runtime.health_check()["enabled"] is True
