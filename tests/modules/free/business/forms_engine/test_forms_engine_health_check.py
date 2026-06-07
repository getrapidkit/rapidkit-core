def test_forms_engine_health_check_counts_forms(rendered_forms_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_forms_engine["vendor"]
    engine = vendor.FormsEngine()
    form = engine.create_form(
        "Contact", [vendor.FormField("email", "Email", vendor.FieldType.EMAIL)]
    )
    engine.submit(form.form_id, {"email": "bad"})

    assert engine.health_check()["forms"] == 1
    assert engine.health_check()["invalid_submissions"] == 1
