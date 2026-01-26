from core.services import validators


def test_is_semver_valid():
    ok, value = validators.is_semver("1.2.3")
    assert ok
    assert value == "1.2.3"


def test_is_semver_invalid():
    ok, value = validators.is_semver("1.2")
    assert not ok
    assert value == "1.2"


def test_always_upper():
    assert validators.always_upper("rapid") == "RAPID"
