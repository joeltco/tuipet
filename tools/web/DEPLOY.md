# Optional web build hook for Claude

Keep this separate from the existing pip publish steps in `tools/deploy.sh`:

```sh
python3 tools/build_web.py
```

The builder requires Python 3.11+, downloads pinned artifacts if the local cache
is empty, verifies SHA-256, and emits `dist/web/`. It does not deploy anything.
Serve that directory at `/tuipet/`, including its versioned `assets/` tree.
`index.html` and the root `manifest.json` must revalidate (`Cache-Control:
no-cache`); `assets/` can have immutable long-lived caching. Retain old published
asset directories during updates so already-loading tabs can finish. The local
builder prunes obsolete local builds; do not mirror-delete published assets
without a retention policy. No service worker is installed in Phase 1.

Keep the existing lobby WebSocket upgrade route at `wss://ff3mmo.com/tuipet/`.
An HTTP navigation to `/tuipet/` serves the static index; an Upgrade request goes
to the existing lobby. No Python server process per browser and no new lobby
protocol or account database are required. HTTPS is needed for Web Locks and
persistent storage APIs. No deploy/nginx changes were made here.

Local preview:

```sh
python3 -m http.server 8098 --directory dist/web
```

`tools/web_smoke.cjs` is separate from pytest. Set `PLAYWRIGHT_MODULE` to an
installed `playwright-core` module and `CHROMIUM` to its browser binary if needed.
Set `WEB_TEST_NAME` and `WEB_TEST_PASSWORD` to explicitly throwaway credentials.
Names are created by the normal server login flow. The script uses the actual
first-run account UI, opens the lobby, checks persistence on reload, captures
screenshots and measures CPU. It sends no chat/invites. It connects to production
by default. `WEB_URL` overrides the preview URL. `WEB_EVIDENCE` overrides output.

For cross-play, run `tools/web_crossplay_client.py` concurrently with a disposable
`HOME`, `TUIPET_SAVE_DIR`, `PYTHONPATH=src`, `WEB_TEST_PEER`, `WEB_TEST_PASSWORD`,
and `WEB_TEST_ROSTER` (JSON output path). It runs the real CPython Textual app
with its headless test driver, uses its sign-in UI and opens its LobbyPanel.
Set `WEB_TEST_PEER` and `WEB_TEST_ROSTER` on the browser smoke process too; both
rosters must include the other account with `live: true`. Create a `.stop` file
beside the roster JSON (same stem) to leave the terminal lobby cleanly. Browser
closure leaves its lobby. Accounts remain on the existing server; its protocol
has no account-deletion command (`wipe` removes a pet save, not an account).
