"""Serialized IDBFS checkpoints. A successful await means local durability."""
import asyncio

_lock = None


async def flush():
    global _lock
    from js import persist
    if _lock is None:
        _lock = asyncio.Lock()
    async with _lock:
        await persist()


def checkpoint():
    from . import is_browser
    if is_browser():
        task = asyncio.create_task(flush())
        task.add_done_callback(_finished)


def _finished(task):
    if not task.cancelled() and task.exception():
        from js import storageError
        storageError(str(task.exception()))
