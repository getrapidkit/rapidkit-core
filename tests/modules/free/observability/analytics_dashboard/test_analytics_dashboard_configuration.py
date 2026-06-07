def test_analytics_dashboard_default_configuration(rendered_analytics_dashboard) -> None:
    vendor = rendered_analytics_dashboard["vendor"]
    config = vendor.build_default_config()

    assert config.enabled is True
    assert config.metadata == {}
