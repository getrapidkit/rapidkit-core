from core.services.env_validator import ENV_SCHEMA, validate_env


def test_validate_env_valid_defaults():
    validated, ok, errors = validate_env({}, ENV_SCHEMA)
    assert ok is True
    assert errors == []
    # a default key must exist
    assert validated["ENV"] in {"development", "production", "staging"}


def test_validate_env_invalid_bool():
    env = {"DEBUG": "notbool"}
    _validated, ok, errors = validate_env(env, ENV_SCHEMA)
    assert ok is False
    assert any("DEBUG" in e for e in errors)


def test_valid_bool_and_defaults():
    env = {"DEBUG": "true", "ENV": "production"}
    schema = {
        "DEBUG": {"type": "bool", "default": False, "required": True},
        "ENV": {
            "type": "str",
            "default": "development",
            "choices": ["development", "production"],
        },
    }
    validated, is_valid, errors = validate_env(env, schema)
    assert is_valid
    assert validated["DEBUG"] is True
    assert validated["ENV"] == "production"


def test_invalid_bool_blocks():
    env = {"DEBUG": "ssss"}
    schema = {"DEBUG": {"type": "bool", "default": False, "required": True}}
    validated, is_valid, errors = validate_env(env, schema)
    assert not is_valid
    assert any("invalid" in e or "not a boolean" in e for e in errors)


def test_lenient_mode_applies_defaults():
    env = {"DEBUG": "ssss"}
    schema = {"DEBUG": {"type": "bool", "default": True, "required": True}}
    validated, is_valid, errors = validate_env(env, schema, lenient=True)
    assert not is_valid
    assert validated["DEBUG"] is True
    assert errors


def test_url_validation():
    env = {"VAULT_URL": "http:///nohost"}
    schema = {
        "VAULT_URL": {
            "type": "url",
            "default": "http://localhost:8200",
            "required": True,
        }
    }
    v, ok, errors = validate_env(env, schema)
    assert not ok
    assert errors


def test_custom_validator_callable():
    from core.services.validators import is_semver

    env = {"VERSION": "1.2.3"}
    schema = {"VERSION": {"custom_validator": is_semver, "default": "0.0.0", "required": True}}
    v, ok, errors = validate_env(env, schema)
    assert ok
    assert v["VERSION"] == "1.2.3"


def test_missing_required_key():
    schema = {
        "API_KEY": {"type": "str", "required": True, "default": None},
    }
    v, ok, errors = validate_env({}, schema)
    assert not ok
    assert any("API_KEY" in e for e in errors)


def test_list_item_validation_failure():
    schema = {"ALLOWED": {"type": "list", "item_validation": r"^[a-z]+$", "default": []}}
    env = {"ALLOWED": "ok,Bad,also_good"}
    v, ok, errors = validate_env(env, schema)
    assert not ok
    assert any("ALLOWED" in e for e in errors)


def test_custom_validator_failure_path():
    def must_start_x(val: str):  # returns tuple (ok, value)
        return (val.startswith("x"), val)

    schema = {"NAME": {"custom_validator": must_start_x, "default": "xval", "required": True}}
    env = {"NAME": "oops"}
    v, ok, errors = validate_env(env, schema)
    assert not ok
    assert v["NAME"] == "xval"  # default applied
    assert any("NAME" in e for e in errors)
