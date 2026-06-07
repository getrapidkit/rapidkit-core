from modules.free.business.approval_engine.generate import ApprovalEngineModuleGenerator


def test_approval_engine_version_matches_manifest() -> None:
    config = ApprovalEngineModuleGenerator().load_module_config()

    assert config["version"] == "0.1.3"
