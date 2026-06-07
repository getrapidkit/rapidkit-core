from pathlib import Path


def test_analytics_dashboard_framework_templates_exist() -> None:
    root = Path("src/modules/free/observability/analytics_dashboard/templates/variants")

    assert (root / "fastapi" / "analytics_dashboard.py.j2").exists()
    assert (root / "nestjs" / "analytics_dashboard.service.ts.j2").exists()
