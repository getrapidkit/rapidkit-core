def test_queue_platform_dead_letters_after_retry_budget(rendered_queue_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_queue_platform["vendor"]
    queue = vendor.QueuePlatform(vendor.QueuePlatformConfig(max_attempts=2))

    queue.enqueue("jobs", {"id": 1})
    first = queue.process_once("jobs", lambda _message: (_ for _ in ()).throw(RuntimeError("boom")))
    first_status = first.status
    second = queue.process_once(
        "jobs", lambda _message: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    assert first_status == vendor.QueueMessageStatus.RETRYING
    assert second.status == vendor.QueueMessageStatus.DEAD_LETTERED
    assert queue.dead_letters()[0].error == "boom"
