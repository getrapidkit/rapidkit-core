from datetime import datetime

from sync_probe import SYNC_PROBE_TIMESTAMP


def test_sync_probe_timestamp_is_iso8601() -> None:
    """The timestamp should be generated in UTC ISO-8601 format."""

    parsed = datetime.strptime(SYNC_PROBE_TIMESTAMP, "%Y-%m-%dT%H:%M:%SZ")
    assert parsed.tzinfo is None
