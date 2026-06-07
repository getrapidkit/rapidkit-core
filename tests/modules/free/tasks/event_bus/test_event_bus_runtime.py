import asyncio


def test_event_bus_delivers_and_records_events(rendered_event_bus) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_event_bus["vendor"]
    bus = vendor.EventBus()
    received = []

    async def handler(event):
        received.append(event.payload["value"])

    bus.subscribe("order.created", handler)
    event = asyncio.run(bus.publish("order.created", {"value": 42}, tenant_id="t1"))

    assert received == [42]
    assert event.status == vendor.EventStatus.DELIVERED
    assert bus.list_events(topic="order.created")[0].tenant_id == "t1"
