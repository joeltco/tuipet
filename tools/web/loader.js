const started = performance.now();
window.metrics = {}; window.errors = [];
const status = document.querySelector('#status');
const term = window.term = new Terminal({cols:80, rows:30, fontSize:16, scrollback:0, theme:{background:'#121212'}});
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
let takeAnswer = null;
window.askTake = label => new Promise(resolve => {
  status.textContent = `Your pet is on ${label}. Take it onto this device? (y/n)`;
  takeAnswer = value => { status.textContent = ''; takeAnswer = null; resolve(value); };
});
window.key = (name, char = null) => {
  if (takeAnswer) { if (name === 'y' || name === 'n') takeAnswer(name === 'y'); return; }
  if (window.browserKey) browserKey(name, char);
};
const keyboard = document.querySelector('#keyboard');
const names = {Enter:'enter',Escape:'escape',ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',' ':'space',Tab:'tab',Backspace:'backspace','?':'question_mark',PageUp:'pageup',PageDown:'pagedown',Delete:'delete',Home:'home',End:'end'};
// Escape is available on the touch bar; printable text stays literal.
const sendText = text => { for (const c of text) { const n = c === '\x1b' ? 'escape' : c === '\n' ? 'enter' : names[c] || c; key(...(window.withMods ? withMods(n, n === c ? c : null) : [n, c === '\x1b' ? null : c])); } };
const resetInput = () => { keyboard.value = ' '; keyboard.setSelectionRange(1,1); };
resetInput();
keyboard.addEventListener('keydown', e => {
  if (e.isComposing || e.key === 'Process' || e.key === 'Unidentified') return;
  e.preventDefault();
  if (e.key.length === 1 && !e.ctrlKey && !e.altKey) sendText(e.key);
  else key(e.ctrlKey ? 'ctrl+' + e.key.toLowerCase() : names[e.key] || e.key, null);
  resetInput();
});
keyboard.addEventListener('beforeinput', e => {
  if (e.isComposing) return;
  if (e.inputType === 'deleteContentBackward' || e.inputType === 'insertLineBreak' || e.inputType === 'insertParagraph') {
    e.preventDefault(); key(e.inputType === 'deleteContentBackward' ? 'backspace' : 'enter'); resetInput();
  }
});
// Android keyboards (Gboard etc.) never send plain key presses: every letter
// arrives as an unfinished "composition" word that only commits on space.  Waiting
// for compositionend meant a lone `l` never reached the game (Joel 2026-10-17:
// "I press L and nothing happens").  Send each composed letter the moment it
// appears, as the difference from what this word already sent.
let composed = '';
const composeTo = text => {
  text = text || '';
  if (text.startsWith(composed)) sendText(text.slice(composed.length));
  else if (composed.startsWith(text)) for (let i = text.length; i < composed.length; i++) key('backspace');
  else { for (let i = 0; i < composed.length; i++) key('backspace'); sendText(text); }
  composed = text;
};
keyboard.addEventListener('compositionstart', () => { composed = ''; });
keyboard.addEventListener('input', e => {
  if (e.isComposing || e.inputType === 'insertCompositionText') { composeTo(e.data); return; }
  if (e.inputType === 'insertFromComposition') return;
  if (e.inputType === 'deleteContentBackward') key('backspace');
  else sendText(e.data ?? keyboard.value.replace(/^ /, ''));
  resetInput();
});
keyboard.addEventListener('compositionend', e => { composeTo(e.data); composed = ''; resetInput(); });
const focusKeyboard = () => keyboard.focus({preventScroll:true});
// Termux-style extra keys (touch screens only, see index.html): fire on pointerdown and keep the
// soft keyboard's focus so a tap never closes it.
const xkeys = document.querySelector('#xkeys');
const mods = {ctrl:false, alt:false};   // Termux: a tapped CTRL/ALT applies to the NEXT key, then clears
const setMod = (m, on) => { mods[m] = on; xkeys.querySelector(`[data-m=${m}]`).classList.toggle('on', on); };
const withMods = (name, char) => {
  if (!mods.ctrl && !mods.alt) return [name, char];
  const out = (mods.ctrl ? 'ctrl+' : '') + (mods.alt ? 'alt+' : '') + name;
  setMod('ctrl', false); setMod('alt', false);
  return [out, null];
};
xkeys.addEventListener('pointerdown', e => {
  const b = e.target.closest('button'); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  if (b.dataset.m) setMod(b.dataset.m, !mods[b.dataset.m]);
  else if (b.dataset.c) key(...withMods(b.dataset.c, b.dataset.c));
  else key(...withMods(b.dataset.k, null));
  focusKeyboard();
});
window.withMods = withMods;
const xkeysHeight = () => getComputedStyle(xkeys).display === 'none' ? 0 : xkeys.getBoundingClientRect().height;
document.addEventListener('pointerup', e => { if (e.isPrimary) focusKeyboard(); });
// Touch compatibility mousedown can blur the input after pointerup.
document.addEventListener('click', focusKeyboard);
let zoom = 1;
try { zoom = Number(localStorage.getItem('tuipet-font-scale')) || 1; } catch {}
zoom = Math.max(.5, Math.min(4, zoom));
let fitting = false;
function fitTerminal() {
  if (fitting) return;
  fitting = true;
  const v = window.visualViewport;
  const screen = document.querySelector('#screen');
  Object.assign(screen.style, {left:(v?.offsetLeft || 0)+'px',top:(v?.offsetTop || 0)+'px',width:(v?.width || innerWidth)+'px',height:((v?.height || innerHeight) - xkeysHeight())+'px'});
  xkeys.style.bottom = Math.max(0, innerHeight - (v ? v.offsetTop + v.height : innerHeight))+'px';
  const box = document.querySelector('#terminal');
  // Orientation from the PHONE, not the box: the on-screen keyboard shrinks the
  // box until portrait reads as landscape, and 30->24 rows scrambled the whole
  // layout every time the keyboard popped up (Joel 2026-10-17).  Keyboard up =
  // same grid, smaller font.
  const landscape = (window.screen?.width || innerWidth) > (window.screen?.height || innerHeight);
  const targetRows = matchMedia('(pointer:coarse)').matches && landscape ? 24 : 30;
  // Measure the renderer's actual rounded cells, rather than assume font metrics.
  const fits = size => {
    term.options.fontSize = size;
    const cell = term._core._renderService.dimensions.css.cell;
    return cell.width*80 <= box.clientWidth && cell.height*targetRows <= box.clientHeight;
  };
  let low=1, high=128;
  while (low < high) { const mid=Math.ceil((low+high)/2); if (fits(mid)) low=mid; else high=mid-1; }
  term.options.fontSize = Math.max(1, Math.round(low*zoom));
  const cell = term._core._renderService.dimensions.css.cell;
  const cols=Math.max(2,Math.min(80,Math.floor(box.clientWidth/cell.width)));
  const rows=Math.max(2,Math.min(targetRows,Math.floor(box.clientHeight/cell.height)));
  term.element.style.width = (cell.width*cols)+'px';
  term.element.style.margin = '0 auto';
  term.resize(cols,rows);
  if (window.browserResize) browserResize(cols,rows);
  if (lastRaster) bridgeRaster(...lastRaster,lastRaster[2].map((_,i)=>i));
  fitting = false;
}
function changeZoom(value) {
  zoom=Math.max(.5,Math.min(4,value));
  try { localStorage.setItem('tuipet-font-scale',String(zoom)); } catch {}
  fitTerminal();
}
window.addEventListener('resize',fitTerminal);
window.visualViewport?.addEventListener('resize',fitTerminal);
window.visualViewport?.addEventListener('scroll',fitTerminal);
document.addEventListener('wheel',e => { if (e.ctrlKey) { e.preventDefault(); changeZoom(zoom*Math.exp(-e.deltaY*.002)); } },{passive:false,capture:true});
let pinch = null;
document.addEventListener('touchstart',e => { if(e.touches.length===2) { pinch=[Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY),zoom]; e.preventDefault(); } },{passive:false,capture:true});
document.addEventListener('touchmove',e => { if(pinch && e.touches.length===2) { e.preventDefault(); changeZoom(pinch[1]*Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY)/pinch[0]); } },{passive:false,capture:true});
document.addEventListener('touchend',() => { pinch=null; });
fitTerminal();
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
browser_resize = entry.browser_resize
game_task = asyncio.create_task(entry.run())
def game_finished(task):
    if not task.cancelled() and task.exception(): storageError(str(task.exception()))
game_task.add_done_callback(game_finished)
`);
  window.browserKey = pyodide.globals.get('browser_key');
  window.browserVisibility = pyodide.globals.get('browser_visibility');
  window.browserResize = pyodide.globals.get('browser_resize');
  fitTerminal();
  metrics.launchMs = performance.now()-started;
  status.textContent = ''; focusKeyboard();
  if (navigator.storage?.persist) await navigator.storage.persist();
} catch(e) { storageError(e); console.error(e); } })();
