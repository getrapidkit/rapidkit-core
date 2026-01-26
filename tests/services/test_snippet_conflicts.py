from __future__ import annotations

import json
from pathlib import Path

from core.services.snippet_injector import inject_snippet_enterprise


def test_inject_marks_conflicted_when_end_marker_missing(tmp_path: Path):
    target = tmp_path / "app.py"
    # Anchor + a malformed existing block (start without end)
    target.write_text(
        "# <<<inject:settings-fields>>>\n" "# <<<inject:settings-fields:x:start>>>\n" "X = 1\n",
        encoding="utf-8",
    )

    tpl = tmp_path / "t.j2"
    tpl.write_text("X = 2\n", encoding="utf-8")

    res = inject_snippet_enterprise(
        destination_path=target,
        template_path=tpl,
        anchor="# <<<inject:settings-fields>>>",
        variables={},
        snippet_metadata={
            "id": "x",
            "version": "1.0.0",
            "priority": 1,
            "template": "t.j2",
            "module_slug": "free/database/db_postgres",
            "context": {},
            "conflict_resolution": "override",
        },
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is False
    assert res["blocked"] is True

    reg = json.loads((tmp_path / ".rapidkit" / "snippet_registry.json").read_text(encoding="utf-8"))
    assert reg["snippets"]["x::app.py"]["status"] == "conflicted"
