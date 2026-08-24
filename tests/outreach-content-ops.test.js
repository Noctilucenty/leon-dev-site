const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const PYTHON = process.env.PYTHON || 'python3';

function tempDir() { return fs.mkdtempSync(path.join(os.tmpdir(), 'leon-acq-ops-')); }

function sourceCsv(dir) {
  const file = path.join(dir, 'candidates.csv');
  const header = 'business_name,wedge,city,website,contact_page_url,observable_workflow_friction,suggested_outreach_angle,language_signal,verified_date,source_url\n';
  const rows = [1, 2, 3].map(number =>
    `Contractor ${number},home_service_contractor,Example,https://contractor${number}.example/,https://contractor${number}.example/contact,The public request path asks visitors to call and does not show a structured estimate form or appointment control,Offer a focused estimate page with project intake acknowledgment and a documented owner handoff,English site content observed,2026-08-23,https://contractor${number}.example/contact`
  ).join('\n');
  fs.writeFileSync(file, header + rows + '\n');
  return file;
}

function run(script, args) {
  return spawnSync(PYTHON, [path.join(ROOT, 'tools', script), ...args], { encoding: 'utf8' });
}

test('weekday outreach automation prepares private review drafts but has no send path', () => {
  const dir = tempDir();
  const source = sourceCsv(dir);
  const state = path.join(dir, 'state.csv');
  const queue = path.join(dir, 'queue');
  const result = run('outreach_ops.py', ['prepare', '--date', '2026-08-24', '--source', source, '--state', state, '--queue-dir', queue, '--limit', '2']);
  assert.equal(result.status, 0, result.stderr);
  const packet = fs.readFileSync(path.join(queue, '2026-08-24', 'review-packet.md'), 'utf8');
  const manifest = JSON.parse(fs.readFileSync(path.join(queue, '2026-08-24', 'manifest.json'), 'utf8'));
  assert.match(packet, /DRAFT — REVIEW REQUIRED — NOTHING SENT/);
  assert.match(packet, /\[VALID POSTAL ADDRESS\]/);
  assert.match(packet, /may make an after-hours estimate request/i);
  assert.equal(manifest.sendCapability, false);
  assert.equal(manifest.count, 2);
  assert.doesNotMatch(fs.readFileSync(path.join(ROOT, 'tools', 'outreach_ops.py'), 'utf8'), /smtplib|nodemailer|sendgrid|resend/i);
});

test('weekday outreach automation blocks weekends and preserves an existing queue', () => {
  const dir = tempDir();
  const source = sourceCsv(dir);
  const args = ['prepare', '--date', '2026-08-23', '--source', source, '--state', path.join(dir, 'state.csv'), '--queue-dir', path.join(dir, 'queue')];
  const result = run('outreach_ops.py', args);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /Saturday or Sunday/);
  assert.equal(fs.existsSync(path.join(dir, 'queue')), false);
});

test('weekly content automation creates one evidence-backed private draft and never publishes', () => {
  const dir = tempDir();
  const source = sourceCsv(dir);
  const output = path.join(dir, 'content');
  const result = run('content_ops.py', ['prepare', '--date', '2026-08-24', '--source', source, '--output', output]);
  assert.equal(result.status, 0, result.stderr);
  const files = fs.readdirSync(output);
  assert.equal(files.filter(file => file.endsWith('.md')).length, 1);
  const draft = fs.readFileSync(path.join(output, files.find(file => file.endsWith('.md'))), 'utf8');
  const manifest = JSON.parse(fs.readFileSync(path.join(output, files.find(file => file.endsWith('.json'))), 'utf8'));
  assert.match(draft, /PRIVATE DRAFT.*NOT PUBLISHED/);
  assert.match(draft, /five-part estimate-path check/i);
  assert.equal(manifest.publicWriteCapability, false);
});

test('Google Business Profile gate defaults online-only work to blocked', () => {
  const dir = tempDir();
  const config = path.join(dir, 'gbp.json');
  const init = run('gbp_gate.py', ['init', '--config', config]);
  assert.equal(init.status, 0, init.stderr);
  const check = run('gbp_gate.py', ['check', '--config', config]);
  assert.equal(check.status, 3);
  assert.match(check.stdout, /BLOCKED/);
  assert.match(check.stdout, /online-only businesses are not eligible/);
  assert.match(check.stdout, /No Google account or Business Profile action was performed/);
});
