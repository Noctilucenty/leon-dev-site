'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const ROOT = path.resolve(__dirname, '..');
const draftsPath = path.join(ROOT, 'content', 'client-success', 'testimonial-drafts.json');
const publicationPath = path.join(ROOT, 'content', 'client-success', 'testimonial-publication.json');

const exactQuoteDigests = [
  'a3584c213a3be5e7a2f9c0ce1730684be20c8a930b20eb8a29f0e9cfd6c93a66',
  'c54e04e25b08d97ef398d2d8e5102c779720d57a2f6a224e0d895d465b45d565',
  '26ee0f5054b3a0e0e83ddb0dd5c647a285dafb5ebf32d02967ecd5b321a51752',
  '570519fb402471091588ffd8b1721dc736ba9bde1eb4d0d134c48906e628fb61',
  '8a824a8f68d727cd32b5b57238171f4686ed31688d9ef2b27dd71e1e50af6c8b',
  '78478396291bed3f4f6c4377f129b0afbadc440758bb40f1a2d4c301b2b3e00f',
  '7ebf96568fe806660ab5d4d6259fb96068d06e1c625bdce576be8544831601cf',
];

test('all seven testimonial drafts remain byte-locked in non-public draft data', () => {
  assert.match(fs.readFileSync(path.join(ROOT, '.gitignore'), 'utf8'), /\/content\/client-success\/testimonial-drafts\.json/);
  if (!fs.existsSync(draftsPath)) return;
  const document = JSON.parse(fs.readFileSync(draftsPath, 'utf8'));
  assert.equal(document.schema_version, 1);
  assert.equal(document.testimonials.length, 7);
  assert.deepEqual(document.testimonials.map(item => crypto.createHash('sha256').update(item.quote).digest('hex')), exactQuoteDigests);
  assert.deepEqual(document.testimonials.map(item => item.id), Array.from({ length: 7 }, (_, i) => `testimonial-${String(i + 1).padStart(2, '0')}`));
  assert.ok(document.testimonials.every(item => item.supplied_rating === 5));
});

test('the tracked public allowlist contains only the two explicitly approved client quotes', () => {
  const publication = JSON.parse(fs.readFileSync(publicationPath, 'utf8'));
  assert.equal(publication.schema_version, 1);
  assert.deepEqual(publication.approved_testimonials.map(item => item.id), ['testimonial-01', 'testimonial-03']);
  assert.ok(publication.approved_testimonials.every(item => item.rating_approval === null));
  if (fs.existsSync(draftsPath)) {
    const drafts = JSON.parse(fs.readFileSync(draftsPath, 'utf8')).testimonials;
    for (const release of publication.approved_testimonials) {
      const draft = drafts.find(item => item.id === release.id);
      assert.ok(draft, `${release.id} has a locked source draft`);
      const payload = {
        id: draft.id,
        project: draft.project,
        attribution: draft.attribution,
        attribution_context: draft.attribution_context,
        quote: draft.quote,
        placement: draft.placement,
      };
      assert.deepEqual(release.approved_payload, payload);
      const digest = crypto.createHash('sha256').update(
        JSON.stringify(payload, Object.keys(payload).sort())
      ).digest('hex');
      assert.equal(release.payload_sha256, digest);
    }
  }
});

test('the public static manifest passes the standalone testimonial release assertion', () => {
  const result = childProcess.spawnSync('python3', ['tools/check_testimonial_release.py'], {
    cwd: ROOT,
    encoding: 'utf8',
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /(?:0|7) drafts preserved; 2 quotes and 0 ratings released/i);
});

test('approved public payloads remain buildable without the private draft queue', t => {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'leon-testimonial-public-'));
  t.after(() => fs.rmSync(tempRoot, { recursive: true, force: true }));
  const target = path.join(tempRoot, 'content', 'client-success');
  fs.mkdirSync(target, { recursive: true });
  fs.copyFileSync(publicationPath, path.join(target, 'testimonial-publication.json'));
  const python = [
    'import sys',
    'from pathlib import Path',
    `sys.path.insert(0, ${JSON.stringify(path.join(ROOT, 'tools'))})`,
    'from testimonial_gate import load_testimonial_release',
    'drafts, released = load_testimonial_release(Path(sys.argv[1]))',
    "assert not drafts and set(released) == {'testimonial-01', 'testimonial-03'}",
  ].join('; ');
  const result = childProcess.spawnSync('python3', ['-c', python, tempRoot], {
    cwd: ROOT,
    encoding: 'utf8',
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);
});

test('missing publication state fails closed', t => {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'leon-testimonial-gate-'));
  t.after(() => fs.rmSync(tempRoot, { recursive: true, force: true }));
  const target = path.join(tempRoot, 'content', 'client-success');
  fs.mkdirSync(target, { recursive: true });
  const python = [
    'import sys',
    'from pathlib import Path',
    `sys.path.insert(0, ${JSON.stringify(path.join(ROOT, 'tools'))})`,
    'from testimonial_gate import load_testimonial_release',
    'load_testimonial_release(Path(sys.argv[1]))',
  ].join('; ');
  const result = childProcess.spawnSync('python3', ['-c', python, tempRoot], {
    cwd: ROOT,
    encoding: 'utf8',
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /cannot read testimonial gate file/i);
});
