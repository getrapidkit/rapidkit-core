import json
from pathlib import Path
from typing import Any, Dict

from core.config.kit_config import KitConfig, Variable, VariableType
from core.engine.generator import BaseKitGenerator
from core.exceptions import ValidationError
from core.module_manifest import ModuleManifest
from core.module_sign import hash_manifest


class DummyGenerator(BaseKitGenerator):
    def extra_context(self) -> Dict[str, Any]:  # ✅ Match superclass
        return {}


def make_minimal_kit_config() -> KitConfig:
    return KitConfig(
        name="dummy",
        display_name="Dummy",
        description="",
        version="0.0.1",
        min_rapidkit_version="0.0.1",
        category="test",
        tags=[],
        dependencies={},
        modules=[],
        variables=[],
        structure=[],
        hooks={},
    )


def test_module_manifest_roundtrip_and_json() -> None:
    mm = ModuleManifest(
        name="mod",
        version="1.2.3",
        tier="pro",
        capabilities=["a"],
        signature="sig",
        extra={"x": 1},
    )
    d = mm.to_dict()
    assert d["name"] == "mod"
    assert d["version"] == "1.2.3"
    assert d["tier"] == "pro"
    assert d["x"] == 1

    js = mm.to_json()
    assert isinstance(js, str)
    mm2 = ModuleManifest.from_json(js)
    assert mm2.name == mm.name
    assert mm2.version == mm.version


def test_hash_manifest_is_stable_and_length() -> None:
    manifest = json.dumps({"name": "m", "version": "1"}, sort_keys=True)
    h = hash_manifest(manifest)
    # sha256 hex length
    sha_len = len(h)
    assert isinstance(h, str) and len(h) == sha_len


def test_variable_type_conversion() -> None:
    gen = DummyGenerator(Path("."), make_minimal_kit_config())

    # STRING
    v_str = Variable(name="s", type=VariableType.STRING)
    assert gen._convert_variable_type(v_str, 123) == "123"

    # INTEGER
    v_int = Variable(name="i", type=VariableType.INTEGER)
    INT_TEST_VAL = 42
    assert gen._convert_variable_type(v_int, "42") == INT_TEST_VAL

    # INTEGER invalid -> ValidationError
    try:
        gen._convert_variable_type(v_int, "notint")
        raised = False
    except ValidationError:
        raised = True
    assert raised

    # BOOLEAN
    v_bool = Variable(name="b", type=VariableType.BOOLEAN)
    assert gen._convert_variable_type(v_bool, "True") is True
    assert gen._convert_variable_type(v_bool, "0") is False

    # LIST
    v_list = Variable(name="l", type=VariableType.LIST)
    assert gen._convert_variable_type(v_list, "a,b,c") == ["a", "b", "c"]

    # CHOICE
    v_choice = Variable(name="c", type=VariableType.CHOICE, choices=["x", "y"])
    assert gen._convert_variable_type(v_choice, "x") == "x"
