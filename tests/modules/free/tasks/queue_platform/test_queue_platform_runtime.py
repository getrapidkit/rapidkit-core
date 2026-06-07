def test_queue_platform_processes_and_acknowledges_message(rendered_queue_platform) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_queue_platform["vendor"]
    queue = vendor.QueuePlatform()
    handled = []

    queue.enqueue("emails", {"to": "user@example.com"}, tenant_id="tenant-a")
    processed = queue.process_once("emails", lambda message: handled.append(message.payload["to"]))

    assert handled == ["user@example.com"]
    assert processed.status == vendor.QueueMessageStatus.ACKED
    assert queue.list_messages(tenant_id="tenant-a")[0].queue == "emails"
