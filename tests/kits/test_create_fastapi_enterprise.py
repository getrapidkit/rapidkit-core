import shutil
from pathlib import Path

import pytest

from core.services.project_creator import ProjectCreatorService


def test_create_fastapi_enterprise(tmp_path: Path) -> None:
    service = ProjectCreatorService()
    out_dir = tmp_path / "out"
    # Ensure output is clean
    if out_dir.exists():
        shutil.rmtree(out_dir)

    # Check if the enterprise kit is available in this tier
    available_kits = service.registry.list_kits_names()
    if "fastapi.enterprise" not in available_kits:
        pytest.skip(
            f"Kit 'fastapi.enterprise' not available in this tier. Available kits: {available_kits}"
        )

    created = service.create_project(
        kit_name="fastapi.enterprise",
        project_name="alef",
        output_dir=out_dir,
        variables={"project_name": "alef", "secret_key": "x"},
        force=True,
        interactive=False,
        debug=False,
        prompt_func=None,
    )

    assert created, "No files were created by generator"
    # Check that the boilerplates directory exists
    assert (out_dir / "boilerplates" / "alef").exists() or any(Path(p).exists() for p in created)
