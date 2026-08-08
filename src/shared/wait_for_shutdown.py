import asyncio
import signal


async def wait_for_shutdown() -> None:
    event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def handle_signal(*_) -> None:
        loop.call_soon_threadsafe(event.set)

    if hasattr(loop, "add_signal_handler"):
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, event.set)
            except NotImplementedError:
                signal.signal(sig, handle_signal)
    else:
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, handle_signal)

    await event.wait()