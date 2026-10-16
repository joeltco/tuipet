/* Run separately from pytest. Requires playwright-core and Chromium.
 * WEB_TEST_NAME/PASSWORD are explicitly throwaway accounts; login creates them.
 * WEB_TEST_PEER + WEB_TEST_ROSTER enable a simultaneous terminal presence proof.
 */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || '/tmp/flattill-staging-tools/node_modules/playwright-core');
const fs = require('fs');
const out = process.env.WEB_EVIDENCE || '_astra/web_build';
async function phase2() {
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM || '/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const report = {viewports:[],errors:[]};
  try {
    for (const [name,width,height] of [['phone-portrait',390,844],['phone-landscape',844,390],['tablet',768,1024],['desktop',1100,800]]) {
      console.log('Checking '+name);
      const context = await browser.newContext({viewport:{width,height},hasTouch:true});
      const page = await context.newPage();
      page.on('pageerror',e=>report.errors.push(String(e)));
      await page.goto(process.env.WEB_URL || 'http://localhost:8098');
      await page.waitForFunction(()=>window.browserKey || window.errors?.length,null,{timeout:90000});
      const mode = n => page.waitForFunction(n=>pyodide.runPython('type(entry.app.mode).__name__')===n,n,{timeout:30000});
      const soft = text => page.locator('#keyboard').evaluate((el,text)=>{
        el.focus(); el.value=' '+text;
        el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:text}));
      },text);
      const enter = () => page.locator('#keyboard').evaluate(el=>el.dispatchEvent(new InputEvent('beforeinput',{bubbles:true,cancelable:true,inputType:'insertLineBreak'})));
      await page.waitForTimeout(2000);
      await enter(); await mode('AccountPanel');
      await soft('abc');
      await page.waitForFunction(()=>pyodide.runPython('entry.app.mode.name_buf')==='abc');
      await page.locator('#keyboard').evaluate(el=>el.dispatchEvent(new InputEvent('beforeinput',{bubbles:true,cancelable:true,inputType:'deleteContentBackward'})));
      await page.waitForFunction(()=>pyodide.runPython('entry.app.mode.name_buf')==='ab');
      await soft('~'); await mode('EggSelectPanel');
      await enter(); await mode('NoneType');
      await page.waitForTimeout(15000);
      await page.screenshot({path:`${out}/${name}-home.png`});
      await soft('g'); await mode('OptionsPanel');
      await page.waitForTimeout(500);
      await page.screenshot({path:`${out}/${name}-menu.png`});
      await soft('g'); await mode('NoneType');
      await page.tap('body', {position:{x:width-5,y:height-5}});
      if(await page.locator('#keyboard').evaluate(el=>document.activeElement!==el)) throw Error('Tap did not focus keyboard');
      await page.setViewportSize({width,height:Math.max(200,Math.floor(height*.6))});
      await page.waitForTimeout(300);
      if(await page.evaluate(()=>term.cols!==80 || term.rows!==30)) throw Error('Keyboard-sized viewport did not refit');
      await page.setViewportSize({width,height});
      await page.waitForTimeout(300);
      const layout = await page.evaluate(()=>({cols:term.cols,rows:term.rows,font:term.options.fontSize,status:document.querySelector('#status').textContent,scroll:document.documentElement.scrollWidth>innerWidth || document.documentElement.scrollHeight>innerHeight,focus:document.activeElement.id,errors}));
      if(layout.status || layout.scroll || layout.errors.length || layout.cols!==80 || layout.rows!==30) throw Error(JSON.stringify(layout));
      const cdp=await context.newCDPSession(page); await cdp.send('Performance.enable');
      const metric=async()=>(await cdp.send('Performance.getMetrics')).metrics.find(m=>m.name==='TaskDuration').value;
      const before=await metric(), start=Date.now(); await page.waitForTimeout(10000);
      const cpuPercent=((await metric())-before)/((Date.now()-start)/1000)*100;
      report.viewports.push({name,width,height,...layout,cpuPercent});
      fs.writeFileSync(out+'/phase2-smoke.json',JSON.stringify(report,null,2));
      if(cpuPercent>=15) throw Error(`${name} CPU ${cpuPercent} >= 15%`);
      await page.keyboard.down('Control'); await page.mouse.wheel(0,-400); await page.keyboard.up('Control');
      await page.waitForTimeout(500);
      const zoom=await page.evaluate(()=>({scale:localStorage.getItem('tuipet-font-scale'),cols:term.cols,rows:term.rows}));
      if(Number(zoom.scale)<=1 || zoom.cols>=77 && zoom.rows>=24) throw Error('Zoom did not resize terminal: '+JSON.stringify(zoom));
      await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:50,y:100},{x:150,y:100}]});
      await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:40,y:100},{x:160,y:100}]});
      await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
      const pinched=await page.evaluate(()=>localStorage.getItem('tuipet-font-scale'));
      if(Number(pinched)<=Number(zoom.scale)) throw Error('Pinch did not zoom');
      zoom.scale=pinched;
      await page.reload(); await page.waitForFunction(()=>window.browserKey,null,{timeout:90000});
      if(await page.evaluate(()=>localStorage.getItem('tuipet-font-scale'))!==zoom.scale) throw Error('Zoom not remembered');
      await context.close();
    }
    if(report.errors.length) throw Error(report.errors.join('\n'));
  } finally { fs.writeFileSync(out+'/phase2-smoke.json',JSON.stringify(report,null,2)); await browser.close(); }
}
(async () => {
  if (process.env.WEB_PHASE2) { await phase2(); return; }
  if (!process.env.WEB_TEST_NAME || !process.env.WEB_TEST_PASSWORD) throw Error('Set throwaway WEB_TEST_NAME and WEB_TEST_PASSWORD');
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM || '/usr/bin/chromium', headless:true, args:['--no-sandbox']});
  const page = await browser.newPage({viewport:{width:1100,height:800}});
  const py = code => page.evaluate(async code => {
    const r = await pyodide.runPythonAsync(code);
    return r?.toJs ? r.toJs({dict_converter:Object.fromEntries}) : r;
  }, code);
  const waitMode = name => page.waitForFunction(name => {
    try { return pyodide.runPython('type(entry.app.mode).__name__') === name; } catch { return false; }
  }, name, {timeout:30000});
  const report = {account:process.env.WEB_TEST_NAME, peer:process.env.WEB_TEST_PEER};
  try {
    await page.goto(process.env.WEB_URL || 'http://localhost:8098');
    await page.waitForFunction(() => window.errors?.length || window.browserKey, null, {timeout:90000});
    await page.waitForTimeout(3000);
    if (await page.evaluate(() => errors.length)) throw Error(await page.evaluate(() => errors.join('\n')));
    await page.keyboard.press('Enter'); await waitMode('AccountPanel');
    await page.keyboard.type(process.env.WEB_TEST_NAME, {delay:30});
    await page.keyboard.press('Tab');
    await page.keyboard.type(process.env.WEB_TEST_PASSWORD, {delay:30});
    await page.keyboard.press('Enter');
    await page.waitForFunction(name => pyodide.runPython('__import__("tuipet.persistence",fromlist=["get_account"]).get_account()[0]')===name && ['EggSelectPanel','NoneType'].includes(pyodide.runPython('type(entry.app.mode).__name__')), process.env.WEB_TEST_NAME, {timeout:30000});
    if (await py('type(entry.app.mode).__name__') === 'EggSelectPanel') await page.keyboard.press('Enter');
    await waitMode('NoneType');
    await page.waitForTimeout(15000);
    await page.screenshot({path:out+'/home.png'});
    const cdp = await page.context().newCDPSession(page); await cdp.send('Performance.enable');
    const metric = async () => (await cdp.send('Performance.getMetrics')).metrics.find(x=>x.name==='TaskDuration').value;
    let before = await metric(), t = Date.now(); await page.waitForTimeout(10000);
    report.home = {seconds:(Date.now()-t)/1000, taskSeconds:(await metric())-before};
    report.home.cpuPercent = report.home.taskSeconds/report.home.seconds*100;
    await py('import cProfile\nprof=cProfile.Profile()\nprof.enable()');
    await page.waitForTimeout(5000);
    const profile = await py("prof.disable()\nimport pstats, io\ns=io.StringIO()\npstats.Stats(prof,stream=s).sort_stats('cumtime').print_stats(30)\ns.getvalue()");
    fs.writeFileSync(out+'/profile.txt', profile);
    await py('await entry.visibility(True)');
    const frame = await py('entry.app.screen_w.frame_i');
    before = await metric(); t=Date.now(); await page.waitForTimeout(5000);
    report.hidden = {seconds:(Date.now()-t)/1000, taskSeconds:(await metric())-before, frameBefore:frame, frameAfter:await py('entry.app.screen_w.frame_i')};
    await py('await entry.visibility(False)');
    await page.keyboard.press('l'); await waitMode('LobbyPanel');
    await page.waitForFunction(() => pyodide.runPython('entry.app.mode.state.connected'), null, {timeout:30000});
    await page.waitForFunction(() => pyodide.runPython('bool(entry.app.mode.state.roster)'), null, {timeout:30000});
    report.webRoster = await py('entry.app.mode.state.roster');
    if (process.env.WEB_TEST_PEER) {
      await page.waitForFunction(peer => pyodide.runPython('entry.app.mode.state.roster').toJs({dict_converter:Object.fromEntries}).some(p=>p.name===peer && p.live), process.env.WEB_TEST_PEER, {timeout:30000});
      report.webRoster = await py('entry.app.mode.state.roster');
      const until=Date.now()+15000;
      while(Date.now()<until) {
        const roster=JSON.parse(fs.readFileSync(process.env.WEB_TEST_ROSTER,'utf8'));
        if(roster.players.some(p=>p.name===process.env.WEB_TEST_NAME && p.live)) { report.terminal=roster; break; }
        await page.waitForTimeout(500);
      }
      if(!report.terminal) throw Error('Terminal never saw browser');
    }
    await page.screenshot({path:out+'/lobby.png'});
    await page.keyboard.press('Escape'); await waitMode('NoneType');
    await py('entry.app.autosave()\nawait entry.durable_save()');
    report.savedAt = await py('entry.persistence.local_saved_at()').catch(()=>py('__import__("tuipet.persistence",fromlist=["local_saved_at"]).local_saved_at()'));
    report.errors = await page.evaluate(()=>errors);
    await page.reload(); await page.waitForFunction(()=>window.browserKey || window.errors?.length,null,{timeout:90000});
    await page.waitForTimeout(5000);
    report.reloadAccount = await py('__import__("tuipet.persistence",fromlist=["get_account"]).get_account()[0]');
    if(report.reloadAccount!==process.env.WEB_TEST_NAME) throw Error('Account did not persist');
    report.reloadPet = await py('entry.app.pet.num');
    if (report.errors.length) throw Error(report.errors.join('\n'));
    await page.screenshot({path:out+'/reload.png'});
    console.log(JSON.stringify(report,null,2));
  } catch(e) {
    report.failure = String(e);
    await page.screenshot({path:out+'/failure.png'}).catch(()=>{});
    report.errors = await page.evaluate(()=>window.errors).catch(()=>[]);
    throw e;
  } finally {
    fs.writeFileSync(out+'/smoke.json',JSON.stringify(report,null,2));
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exit(1)});
