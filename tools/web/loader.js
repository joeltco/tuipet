const started = performance.now();
window.metrics = {}; window.errors = [];
const status = document.querySelector('#status');
const term = window.term = new Terminal({cols:80, rows:30, fontSize:16, theme:{background:'#101010'}});
term.open(document.querySelector('#terminal'));
term.loadAddon(new CanvasAddon.CanvasAddon());
// Only the LCD's existing half-block pixel colors use this canvas; all game
// UI, keyboard routing, panels and timing still belong to the Python app.
const lcd = document.createElement('canvas');
lcd.style.cssText = 'position:absolute;pointer-events:none;z-index:10;display:none;image-rendering:pixelated';
term.element.append(lcd);
let lastRaster = null;
window.bridgeRaster = (x, y, colors, changed) => {
  const cell = term._core._renderService.dimensions.css.cell;
  const w = cell.width, h = cell.height;
  if (lcd.width !== 40 || lcd.height !== 24) {
    lcd.width = 40; lcd.height = 24; changed = colors.map((_, i) => i);
  }
  Object.assign(lcd.style, {display:'block',left:(x*w)+'px',top:(y*h)+'px',width:(w*40)+'px',height:(h*12)+'px'});
  const ctx = lcd.getContext('2d');
  for (const row of changed) for (let col=0;col<40;col++) {
    ctx.fillStyle = colors[row][col][0]; ctx.fillRect(col,row*2,1,1);
    ctx.fillStyle = colors[row][col][1]; ctx.fillRect(col,row*2+1,1,1);
  }
  lastRaster = [x,y,colors];
};
window.bridgeRasterHide = () => { lcd.style.display='none'; lastRaster=null; };
window.addEventListener('resize', () => {
  if (lastRaster) bridgeRaster(...lastRaster,lastRaster[2].map((_,i)=>i));
});
let output = '', scheduled = false;
window.bridgeWrite = s => {
  output += s;
  if (!scheduled) { scheduled = true; requestAnimationFrame(() => {
    term.write(output); output = ''; scheduled = false;
    metrics.writes = (metrics.writes || 0) + 1;
  }); }
};
window.storageError = e => { errors.push(String(e)); status.textContent = 'Save failed: ' + e; };
window.persist = () => new Promise((resolve, reject) => pyodide.FS.syncfs(false, e => e ? reject(e) : resolve()));
window.askTake = label => new Promise(resolve => {
  status.textContent = `Your pet is on ${label}. Take it onto this device? `;
  for (const [text, value] of [['Take pet', true], ['Leave there', false]]) {
    const b = document.createElement('button'); b.textContent = text;
    b.onclick = () => { status.replaceChildren(); resolve(value); }; status.append(b);
  }
});
window.key = (key, char = null) => { if (window.browserKey) browserKey(key, char); };
term.onKey(({domEvent:e}) => {
  e.preventDefault();
  const map = {Enter:'enter',Escape:'escape',ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',' ':'space',Tab:'tab',Backspace:'backspace','?':'question_mark',PageUp:'pageup',PageDown:'pagedown',Delete:'delete',Home:'home',End:'end'};
  const k = map[e.key] || (e.ctrlKey ? 'ctrl+' + e.key.toLowerCase() : e.key);
  key(k, e.key.length === 1 ? e.key : null);
});
document.addEventListener('visibilitychange', () => {
  if (window.browserVisibility) browserVisibility(document.hidden).catch(storageError);
});
window.addEventListener('pagehide', () => {
  if (window.browserVisibility) browserVisibility(true).catch(storageError);
});
(async () => { try {
  // Lock the save across tabs; IDBFS cannot merge two in-memory filesystems.
  let unlock;
  const held = new Promise(resolve => { unlock = resolve; });
  if (navigator.locks) await new Promise((resolve, reject) => {
    navigator.locks.request('tuipet-save', {ifAvailable:true}, async lock => {
      if (!lock) { reject(Error('tuipet is already open in another tab.')); return; }
      resolve(); await held;
    }).catch(reject);
  });
  window.pyodide = await loadPyodide({indexURL:ASSET_ROOT+'vendor/'});
  metrics.runtimeMs = performance.now()-started;
  const manifest = await (await fetch(ASSET_ROOT+'manifest.json')).json();
  for (const wheel of manifest.wheels) pyodide.unpackArchive(await (await fetch(ASSET_ROOT+'vendor/'+wheel)).arrayBuffer(), 'zip', {extractDir:'/lib/python3.12/site-packages'});
  pyodide.unpackArchive(await (await fetch(ASSET_ROOT+'game.zip')).arrayBuffer(), 'zip', {extractDir:'/game'});
  pyodide.FS.mkdirTree('/saves'); pyodide.FS.mount(pyodide.FS.filesystems.IDBFS, {}, '/saves');
  await new Promise((resolve,reject) => pyodide.FS.syncfs(true,e=>e?reject(e):resolve()));
  await pyodide.runPythonAsync(`
import sys, asyncio
sys.path.insert(0, '/game')
from tuipet.web import entry
from js import storageError
from pyodide.ffi import create_proxy
browser_key = entry.browser_key
browser_visibility = create_proxy(entry.visibility)
game_task = asyncio.create_task(entry.run())
def game_finished(task):
    if not task.cancelled() and task.exception(): storageError(str(task.exception()))
game_task.add_done_callback(game_finished)
`);
  window.browserKey = pyodide.globals.get('browser_key');
  window.browserVisibility = pyodide.globals.get('browser_visibility');
  metrics.launchMs = performance.now()-started;
  status.textContent = 'tuipet '+manifest.version+' · keyboard edition'; term.focus();
  if (navigator.storage?.persist) await navigator.storage.persist();
} catch(e) { storageError(e); console.error(e); } })();
