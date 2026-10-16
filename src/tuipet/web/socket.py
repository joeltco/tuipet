"""Browser text WebSocket with the async interface used by net.py."""
import asyncio


class BrowserSocket:
    def __init__(self, uri, *, max_size=262144, open_timeout=6, **kwargs):
        self.uri, self.max_size, self.timeout = uri, max_size, open_timeout
        self.queue = asyncio.Queue(maxsize=64)
        self.callbacks = []
        self.closed = False

    def _closed(self, event=None):
        self.closed = True
        if not self.opened.done():
            self.opened.set_exception(ConnectionError('WebSocket failed'))
        if self.queue.full():
            self.queue.get_nowait()
        self.queue.put_nowait(None)

    async def __aenter__(self):
        from js import WebSocket
        from pyodide.ffi import create_proxy
        self.opened = asyncio.get_running_loop().create_future()
        self.socket = WebSocket.new(self.uri)

        def opened(event):
            if not self.opened.done():
                self.opened.set_result(None)

        def message(event):
            data = str(event.data)
            if len(data.encode('utf-8')) > self.max_size or self.queue.full():
                self.socket.close(1009)
                self._closed()
            elif not self.closed:
                self.queue.put_nowait(data)

        for name, fn in [('open', opened), ('error', self._closed),
                         ('close', self._closed), ('message', message)]:
            callback = create_proxy(fn)
            self.callbacks.append((name, callback))
            self.socket.addEventListener(name, callback)
        try:
            await asyncio.wait_for(self.opened, self.timeout)
        except BaseException:
            await self.close()
            raise
        return self

    async def send(self, data):
        if not isinstance(data, str):
            raise TypeError('tuipet WebSocket messages must be text')
        if self.closed or self.socket.readyState != 1:
            raise ConnectionError('WebSocket closed')
        deadline = asyncio.get_running_loop().time() + self.timeout
        while self.socket.bufferedAmount > self.max_size:
            if self.closed or self.socket.readyState != 1:
                raise ConnectionError('WebSocket closed')
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError('WebSocket send buffer stalled')
            await asyncio.sleep(0.01)
        self.socket.send(data)

    async def recv(self):
        if self.closed and self.queue.empty():
            raise ConnectionError('WebSocket closed')
        data = await self.queue.get()
        if data is None:
            raise ConnectionError('WebSocket closed')
        return data

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self.recv()
        except ConnectionError:
            raise StopAsyncIteration

    async def close(self):
        self.socket.close()
        self._closed()
        for name, callback in self.callbacks:
            self.socket.removeEventListener(name, callback)
            callback.destroy()
        self.callbacks.clear()

    async def __aexit__(self, *args):
        await self.close()


connect = BrowserSocket
