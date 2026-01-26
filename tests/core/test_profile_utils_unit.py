from core.services import profile_utils


def test_resolve_profile_chain_handles_inheritance():
    config = {
        "profiles": [
            "base",
            "dev: inherits base",
            "prod: inherits dev",
        ]
    }

    chain = profile_utils.resolve_profile_chain("prod", config)

    assert chain == ["base", "dev", "prod"]


def test_resolve_profile_chain_breaks_on_cycle():
    config = {"profiles": ["loop: inherits loop"]}

    chain = profile_utils.resolve_profile_chain("loop", config)

    # cycle should break after first encounter
    assert chain == ["loop"]


def test_resolve_profile_chain_supports_dict_metadata() -> None:
    config = {
        "profiles": {
            "fastapi/standard": {"description": "Base FastAPI"},
            "fastapi/ddd": {
                "description": "DDD FastAPI",
                "inherits": "fastapi/standard",
            },
        }
    }

    chain = profile_utils.resolve_profile_chain("fastapi/ddd", config)

    assert chain == ["fastapi/standard", "fastapi/ddd"]
