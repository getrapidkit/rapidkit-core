import asyncio


def test_event_bus_dead_letters_failed_delivery(rendered_event_bus) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_event_bus["vendor"]
    bus = vendor.EventBus(vendor.EventBusConfig(max_attempts=2))

    async def broken(_event):
        raise RuntimeError("boom")

    bus.subscribe("fail", broken)
    event = asyncio.run(bus.publish("fail", {"value": 1}))

    assert event.status == vendor.EventStatus.DEAD_LETTERED
    assert event.attempts == 2
    assert bus.dead_letters()[0].error == "boom"
