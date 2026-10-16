"""Run the real CPython Textual app headlessly as a throwaway presence peer.

Uses the normal account UI and lobby action; sends no chat or game invitations.
Always set HOME and TUIPET_SAVE_DIR to a disposable directory before running.
"""
import asyncio
import json
import os
from pathlib import Path

from tuipet import persistence
from tuipet.app import TuiPetApp
from tuipet.appboot import warm_data


async def wait_for(predicate, timeout=30):
    async def poll():
        while not predicate():
            await asyncio.sleep(0.1)
    await asyncio.wait_for(poll(), timeout)


async def main():
    if not os.environ.get('TUIPET_SAVE_DIR'):
        raise RuntimeError('Set a disposable TUIPET_SAVE_DIR and HOME')
    name, pw = os.environ['WEB_TEST_PEER'], os.environ['WEB_TEST_PASSWORD']
    warm_data()
    persistence.set_auto_update(False)
    app = TuiPetApp()
    app.sound = False
    roster = Path(os.environ['WEB_TEST_ROSTER'])
    async with app.run_test(size=(80, 30)) as pilot:
        await pilot.press('enter')
        await wait_for(lambda:type(app.mode).__name__ == 'AccountPanel')
        await pilot.press(*name, 'tab', *pw, 'enter')
        await wait_for(lambda:persistence.get_account()[0] == name
                       and type(app.mode).__name__ in ('EggSelectPanel', 'NoneType'))
        if type(app.mode).__name__ == 'EggSelectPanel':
            await pilot.press('enter')
        await pilot.press('l')
        await wait_for(lambda:type(app.mode).__name__ == 'LobbyPanel'
                       and app.mode.state is not None)
        try:
            for _ in range(300):
                state = app.mode.state
                roster.write_text(json.dumps({
                    'connected': state.connected, 'players': state.roster,
                    'error': state.error, 'client': 'TuiPetApp CPython run_test',
                }, default=str), encoding='utf-8')
                if roster.with_suffix('.stop').exists():
                    break
                await asyncio.sleep(1)
        finally:
            await pilot.press('escape')


if __name__ == '__main__':
    asyncio.run(main())
