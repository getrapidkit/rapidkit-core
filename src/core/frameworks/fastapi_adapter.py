"""FastAPI framework adapter implementation (initial stub).

Future: implement detection logic & artifact generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from .base import GeneratedArtifact


class FastAPIFrameworkAdapter:  # pragma: no cover - minimal stub
    name = "fastapi"

    @classmethod
    def detect(cls, project_root: str) -> bool:
        root = Path(project_root)
        # Heuristic: pyproject.toml contains fastapi OR app/main.py / backend/main.py exists
        pyproject = root / "pyproject.toml"
        try:
            if pyproject.exists():
                text = pyproject.read_text(encoding="utf-8", errors="ignore")
                if "fastapi" in text.lower():
                    return True
        except (OSError, UnicodeDecodeError):  # pragma: no cover - IO issues
            pass
        for candidate in [
            root / "app" / "main.py",
            root / "backend" / "main.py",
            root / "src" / "app" / "main.py",
        ]:
            if candidate.exists():
                return True
        return False

    @classmethod
    def initialize_project(
        cls, project_root: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        # Minimal bootstrap; richer kit-based generation handled elsewhere.
        project_name = options.get("project_name", "app")
        base_pkg = options.get("package", project_name)
        files: List[GeneratedArtifact] = [
            GeneratedArtifact(
                path=f"{base_pkg}/main.py",
                content=(
                    "from fastapi import FastAPI\n\n"
                    f'app = FastAPI(title="{project_name}")\n\n'
                    "@app.get('/')\n"
                    "def read_root():\n"
                    "    return {'status': 'ok'}\n"
                ),
            ),
            GeneratedArtifact(
                path="requirements.txt",
                content="fastapi\nuvicorn\n",
                overwrite=False,
            ),
        ]
        if options.get("include_tests", True):
            files.append(
                GeneratedArtifact(
                    path="tests/test_health.py",
                    content=(
                        "from fastapi.testclient import TestClient\n"
                        f"from {base_pkg}.main import app\n\n"
                        "client = TestClient(app)\n\n"
                        "def test_root():\n"
                        "    r = client.get('/')\n"
                        "    assert r.status_code == 200\n"
                        "    assert r.json()['status'] == 'ok'\n"
                    ),
                )
            )
        return files

    @classmethod
    def add_module(
        cls, project_root: str, module: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        # Provide a simple router stub for a module
        base_pkg = options.get("package", "app")
        router_path = f"{base_pkg}/routers/{module}.py"
        return [
            GeneratedArtifact(
                path=router_path,
                content=(
                    "from fastapi import APIRouter\n\n"
                    f"router = APIRouter(prefix='/{module}', tags=['{module}'])\n\n"
                    "@router.get('/')\n"
                    "def list_items():\n"
                    "    return {'items': []}\n"
                ),
                overwrite=False,
            )
        ]

    @classmethod
    def add_resource(
        cls, project_root: str, resource: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        base_pkg = options.get("package", "app")
        model_name = resource.capitalize()
        return [
            GeneratedArtifact(
                path=f"{base_pkg}/models/{resource}.py",
                content=(
                    "from pydantic import BaseModel\n\n"
                    f"class {model_name}(BaseModel):\n"
                    "    id: int\n"
                    "    name: str\n"
                ),
                overwrite=False,
            )
        ]

    @classmethod
    def normalize_options(cls, options: Dict[str, Any]) -> Dict[str, Any]:
        return options
