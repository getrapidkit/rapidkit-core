def test_forms_engine_records_validation_errors(rendered_forms_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_forms_engine["vendor"]
    engine = vendor.FormsEngine()
    form = engine.create_form(
        "Contact", [vendor.FormField("email", "Email", vendor.FieldType.EMAIL, required=True)]
    )

    submission = engine.submit(form.form_id, {"email": "bad"})

    assert submission.valid is False
    assert submission.errors == {"email": "invalid_email"}


def test_forms_engine_rejects_duplicate_fields(rendered_forms_engine) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_forms_engine["vendor"]
    engine = vendor.FormsEngine()

    try:
        engine.create_form(
            "Bad", [vendor.FormField("email", "Email"), vendor.FormField("email", "Email 2")]
        )
    except vendor.FormsEngineError as exc:
        assert "duplicate field" in str(exc)
    else:
        raise AssertionError("expected FormsEngineError")
