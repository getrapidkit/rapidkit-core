def test_forms_engine_validates_and_exports_submissions(rendered_forms_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_forms_engine["vendor"]
    engine = vendor.FormsEngine()
    form = engine.create_form(
        "Lead",
        [
            vendor.FormField("email", "Email", vendor.FieldType.EMAIL, required=True),
            vendor.FormField("plan", "Plan", vendor.FieldType.SELECT, options=("starter", "pro")),
        ],
        tenant_id="tenant-a",
    )

    submission = engine.submit(
        form.form_id, {"email": "buyer@example.com", "plan": "pro"}, tenant_id="tenant-a"
    )

    assert submission.valid is True
    assert "buyer@example.com" in engine.export_csv(form.form_id)
