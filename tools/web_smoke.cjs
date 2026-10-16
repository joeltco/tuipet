/* Run separately from pytest. Requires playwright-core and Chromium.
 * WEB_TEST_NAME/PASSWORD are explicitly throwaway accounts; login creates them.
 * WEB_TEST_PEER + WEB_TEST_ROSTER enable a simultaneous terminal presence proof.
 */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || '/tmp/flattill-staging-tools/node_modules/playwright-core');
const fs = require('fs');
const out = process.env.WEB_EVIDENCE || '_astra/web_build';
(async () => {
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
