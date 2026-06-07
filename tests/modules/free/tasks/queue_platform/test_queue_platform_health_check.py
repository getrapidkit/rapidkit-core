def test_queue_platform_health_check_counts_queue_state(rendered_queue_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_queue_platform["vendor"]
    queue = vendor.QueuePlatform()

    queue.enqueue("jobs", {"id": 1})
    queue.lease("jobs")

    assert queue.health_check()["leased"] == 1
    assert queue.health_check()["messages"] == 1
