"""Browser bootstrap: same first-run UI, cloud cartridge and game as the CLI."""
import os

from . import is_browser

app = None
hidden = False


def browser_key(key, char=None):
    if app is not None and not hidden:
        from .driver import key_event
        app.post_message(key_event(key, char))


def browser_resize(cols, rows):
    if app is not None:
        from textual import events
        from textual.geometry import Size
        size = Size(cols, rows)
        app.post_message(events.Resize(size, size))
        from ..appboot import MIN_COLS, MIN_ROWS, terminal_size_warning
        if (cols < MIN_COLS or rows < MIN_ROWS) and size != getattr(app, '_web_warn_size', None):
            app.notify(terminal_size_warning(cols, rows), timeout=2.5)
        app._web_warn_size = size


async def visibility(value):
    global hidden
    hidden = bool(value)
    if app is not None:
        for name in ("_frame_timer", "_life_timer", "_save_timer"):
            timer = getattr(app, name, None)
            if timer is not None:
                timer.pause() if hidden else timer.reset()
    if app is not None and hidden:
        app.autosave()
        app._flush_dms_on_quit()
        await durable_save()


async def durable_save():
    from .storage import flush
    await flush()


async def run():
    global app
    if not is_browser():
        raise RuntimeError("The web entry point requires Pyodide")
    os.environ.update(HOME="/saves", TUIPET_SAVE_DIR="/saves/tuipet",
                      TERM="xterm-256color", COLORTERM="truecolor", TEXTUAL_FPS="10")
    from .. import persistence
    from ..appboot import warm_data, _lobby_uri
    from ..app import TuiPetApp
    from . import cloud
    from js import askTake
    warm_data()
    name, pw = persistence.get_account()
    if name and persistence.sync_enabled():
        st, save, holder = await cloud.gate(_lobby_uri(), name, pw, cloud.BOOT_TIMEOUT)
        if st == "offline":
            st, save, holder = await cloud.gate(_lobby_uri(), name, pw, cloud.BOOT_TIMEOUT)
        if st == "ok" and holder and holder.get("device") != persistence.device_id():
            persistence.set_holder_cache(False)
            if not await askTake(holder.get("label") or "another device"):
                await durable_save()
                return
            ok, save = await cloud.take(_lobby_uri(), name, pw)
            if not ok:
                raise RuntimeError("Couldn't take the pet. Please reconnect and reload.")
            if save:
                pet, _ = persistence.pet_from_save(dict(save), strict=True)
                if pet is None:
                    raise RuntimeError("Cloud save is unreadable; kept your local save.")
                persistence.rescue_copy()
                persistence.write_save_dict(save)
            persistence.set_holder_cache(True)
        elif st == "ok":
            persistence.set_holder_cache(True)
            await cloud.sync_down_at_startup(_lobby_uri(), name, pw)
        elif st == "offline" and persistence.holder_cache() is False:
            raise RuntimeError("Your pet is on another device. Reconnect to take it here.")
    await durable_save()
    app = TuiPetApp()
    # Cap Textual rendering, without changing the game's 10 Hz simulation clock.
    app.sound = False
    try:
        await app.run_async(size=(80, 30))
    finally:
        persistence.save(app.pet)
        if persistence.sync_enabled() and persistence.holder_cache() is not False:
            name, pw = persistence.get_account()
            if name:
                await cloud.push_save(_lobby_uri(), name, pw, persistence.to_save_dict(app.pet))
        await durable_save()
