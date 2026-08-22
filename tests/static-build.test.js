'use strict';

const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const SCRIPT = path.join(ROOT, 'tools', 'build_static.py');
const TEMP = fs.mkdtempSync(path.join(os.tmpdir(), 'leon-static-build-'));

after(() => {
  fs.rmSync(TEMP, { recursive: true, force: true });
});

function run(args) {
  return spawnSync('python3', [SCRIPT, ...args], {
    cwd: ROOT,
    encoding: 'utf8',
    maxBuffer: 2 * 1024 * 1024
  });
}

function diagnostic(result) {
  return `status=${result.status}\nstdout=${result.stdout}\nstderr=${result.stderr}`;
}

function walkFiles(directory) {
  const out = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      for (const nested of walkFiles(absolute)) out.push(path.join(entry.name, nested));
    } else {
      out.push(entry.name);
    }
  }
  return out.sort();
}

test('--check validates the manifest without creating output', () => {
  const parent = path.join(TEMP, 'readonly');
  const output = path.join(parent, 'dist');
  fs.mkdirSync(parent);

  const result = run(['--check', '--output', output]);
  assert.equal(result.status, 0, diagnostic(result));
  assert.equal(fs.existsSync(output), false);
  assert.match(result.stdout, /manifest validated read-only/);
});

test('static build publishes only pages and required referenced assets', () => {
  const parent = path.join(TEMP, 'public');
  const output = path.join(parent, 'dist');
  fs.mkdirSync(parent);

  let result = run(['--output', output]);
  assert.equal(result.status, 0, diagnostic(result));

  for (const relative of [
    'index.html', 'about.html', 'privacy.html', 'quote.html', 'call.html',
    'services/index.html', 'services/websites.html', 'es/index.html',
    'styles.css', 'assist.css', 'app.js', 'assist.js',
    'assets/favicon.svg', 'assets/og.png', 'favicon.ico', 'apple-touch-icon.png',
    'sitemap.xml', 'robots.txt', 'llms.txt',
    'google632f06756dffc4ba.html', 'b20f1e412f2cff8af636fe5676cfdbcd.txt'
  ]) {
    const published = path.join(output, relative);
    assert.equal(fs.existsSync(published) && fs.statSync(published).isFile(), true, relative);
  }

  for (const relative of [
    'content/publication-ledger.csv', 'content/posts.md',
    'tests/static-build.test.js', 'tools/build_static.py',
    'server/index.js', 'data/events.jsonl', 'research',
    'package.json', 'package-lock.json', 'README.md', 'render.yaml', '.env',
    'assets/facebook.png', 'assets/listings/fb_en_1hook.png',
    'assets/social/ig_01_prices.png'
  ]) {
    assert.equal(fs.existsSync(path.join(output, relative)), false, relative);
  }

  const files = walkFiles(output);
  assert.equal(files.some(file => /^(content|data|research|server|tests|tools)(\/|$)/.test(file)), false);
  assert.equal(files.some(file => /\.(csv|json|md|py|ya?ml)$/i.test(file)), false);

  // A stale expected file is reported, never silently repaired by --check.
  const builtIndex = path.join(output, 'index.html');
  const expectedIndex = fs.readFileSync(builtIndex, 'utf8');
  fs.writeFileSync(builtIndex, 'stale but allowlisted output\n');
  result = run(['--check', '--output', output]);
  assert.notEqual(result.status, 0, diagnostic(result));
  assert.equal(fs.readFileSync(builtIndex, 'utf8'), 'stale but allowlisted output\n');

  // A repeat build may update expected generated files, after which the
  // read-only check verifies byte-for-byte currency.
  result = run(['--output', output]);
  assert.equal(result.status, 0, diagnostic(result));
  assert.equal(fs.readFileSync(builtIndex, 'utf8'), expectedIndex);
  result = run(['--check', '--output', output]);
  assert.equal(result.status, 0, diagnostic(result));
});

test('unexpected preexisting output aborts before any public file is written', () => {
  const parent = path.join(TEMP, 'poisoned');
  const output = path.join(parent, 'dist');
  const leaked = path.join(output, 'content', 'publication-ledger.csv');
  fs.mkdirSync(path.dirname(leaked), { recursive: true });
  fs.writeFileSync(leaked, 'must remain untouched\n');

  const result = run(['--output', output]);
  assert.notEqual(result.status, 0, diagnostic(result));
  assert.match(result.stderr, /outside the public manifest/);
  assert.equal(fs.readFileSync(leaked, 'utf8'), 'must remain untouched\n');
  assert.equal(fs.existsSync(path.join(output, 'index.html')), false);
});

test('unsafe output roots are refused', () => {
  for (const output of [
    ROOT,
    path.join(TEMP, 'not-the-dist-directory'),
    path.join(path.parse(ROOT).root, 'dist'),
    path.join(os.homedir(), 'dist')
  ]) {
    const result = run(['--output', output]);
    assert.notEqual(result.status, 0, diagnostic(result));
    assert.match(result.stderr, /output directory must be named 'dist'|refusing repository|refusing broad output/);
  }
});
