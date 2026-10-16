"""Textual ANSI driver for xterm.js; JS imports stay inside browser methods."""
from textual.driver import Driver
from textual import events
from textual.geometry import Size


def key_event(key, char=None):
    return events.Key(key, char)


class BrowserDriver(Driver):
    def write(self, data):
        from js import bridgeWrite
        bridgeWrite(data)

    def start_application_mode(self):
        self.write("\x1b[?25l")
        from js import term
        size = Size(term.cols, term.rows)
        self._app.post_message(events.Resize(size, size))

    def disable_input(self):
        pass

    def stop_application_mode(self):
        pass
