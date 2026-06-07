def test_forms_engine_vendor_exports_contract(rendered_forms_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_forms_engine["vendor"]

    for name in ("FormsEngine", "FormsEngineConfig", "FormsEngineError", "FormField", "FieldType"):
        assert hasattr(vendor, name)
