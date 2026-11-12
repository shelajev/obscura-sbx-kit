import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import puppeteer from 'puppeteer-core';

const dir = await mkdtemp(join(tmpdir(), 'obscura-cdp-'));
const ready = join(dir, 'ready');
const binary = process.env.OBSCURA_BINARY || 'obscura';
const serverArgs = ['serve', '--host', '127.0.0.1', '--port', '0', '--ready-file', ready];
const image = process.env.OBSCURA_DOCKER_IMAGE;
const server = spawn(image ? 'docker' : binary, image ?
  ['run', '--rm', '--network', 'host', '--user', String(process.getuid()),
   '-v', `${dir}:${dir}`, '--entrypoint', '/usr/local/bin/obscura', image, ...serverArgs] : serverArgs,
  {stdio: ['ignore', 'ignore', 'pipe']});
let logs = '';
server.stderr.on('data', data => { logs += data; });
let browser;
try {
  let address;
  for (let i = 0; i < 200; i++) {
    if (server.exitCode !== null) throw new Error(logs);
    try { address = (await readFile(ready, 'utf8')).trim(); break; }
    catch { await new Promise(resolve => setTimeout(resolve, 50)); }
  }
  assert.ok(address, `CDP readiness timed out: ${logs}`);
  const info = JSON.parse(address);
  assert.equal(info.host, '127.0.0.1');
  console.log('Ready:', info);
  const port = info.port || Number(info.address?.split(':').at(-1));
  const browserURL = `http://127.0.0.1:${port}`;
  browser = await puppeteer.connect({browserURL, defaultViewport: null});
  const page = await browser.newPage();
  await page.goto('data:text/html,<title>CDP fixture</title><button id="b" onclick="this.textContent=\'Clicked\'">Go</button>');
  await page.click('#b');
  assert.equal(await page.$eval('#b', node => node.textContent), 'Clicked');
  assert.equal(await page.title(), 'CDP fixture');
  const png = await page.screenshot({type: 'png'});
  assert.equal(Buffer.from(png).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
  console.log('PASS: Puppeteer CDP navigation, click, evaluation, PNG');
  await page.close();
} finally {
  if (browser) browser.disconnect();
  server.kill('SIGTERM');
  await new Promise(resolve => { if (server.exitCode !== null) resolve(); else server.once('exit', resolve); });
  await rm(dir, {recursive: true, force: true});
}
