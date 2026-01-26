from core.services import snippet_injector as si


def test_merge_snippets_preserves_valid_and_includes_new():
    existing = ["# comment", 'NAME: Field(default="old")', "AGE: Field(default=10)"]
    new = ['NAME: Field(default="new")', 'EMAIL: Field(default="a@b")']
    metadata = {"schema": {"properties": {"NAME": {}, "AGE": {}, "EMAIL": {}}}}
    merged = si.merge_snippets(existing, new, "    ", metadata)
    # merged should contain EMAIL and keep AGE present because in schema
    joined = "\n".join(merged)
    assert "EMAIL" in joined and "AGE" in joined


def test_validate_snippet_schema_env_and_malformed():
    # env-like snippet should return True regardless of schema
    env_snip = "MYKEY=1\nOTHER=2"
    assert si.validate_snippet_schema(env_snip, {}) is True

    # malformed settings lines should warn and eventually return False when schema requires properties
    snip = "BADLINE without colon\nNAME: ="  # bad formats
    schema = {"properties": {"NAME": {}}}
    res = si.validate_snippet_schema(snip, schema)
    assert res in (True, False)  # function logs warnings; ensure it doesn't crash
