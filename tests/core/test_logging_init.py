"""
Tests for core logging module.
"""

from runtime.core.logging import __all__


class TestLoggingModule:
    """Test logging module initialization."""

    def test_logging_module_all_exports(self) -> None:
        """Test that __all__ is properly defined."""
        expected = {
            "get_logger",
            "set_request_context",
            "RequestContextMiddleware",
            "LoggingConfig",
            "OTelBridgeHandler",
            "MetricsBridgeHandler",
            "NoiseFilter",
            "RedactionFilter",
            "ContextEnricher",
            "JsonFormatter",
            "ColoredFormatter",
            "create_stream_handler",
            "create_file_handler",
            "create_syslog_handler",
            "create_queue_handler",
            "setup_queue_listeners",
            "shutdown_queue",
            "get_logging_metadata",
            "refresh_vendor_module",
        }

        assert isinstance(__all__, list)
        assert set(__all__) == expected
