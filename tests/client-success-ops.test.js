const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const TOOL = path.join(ROOT, 'tools', 'client_success_ops.py');
const SLOTS = path.join(ROOT, 'content', 'client-success', 'case-study-slots.json');
const STATE = path.join(ROOT, 'data', 'client-success.json');
const QUEUE = path.join(ROOT, 'data', 'client-success-queue.json');
const TESTIMONIAL_DRAFTS = path.join(ROOT, 'content', 'testimonial-request-pack.md');

const readJson = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));
const sha256 = (value) => crypto.createHash('sha256').update(value).digest('hex');

function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, sorted(value[key])]));
  }
  return value;
}

function publicationDigest(value) {
  return sha256(JSON.stringify(sorted(value)));
}

function run(paths, commandArgs) {
  return spawnSync('python3', [
    TOOL,
    '--slots', paths.slots,
    '--state', paths.state,
    '--queue', paths.queue,
    ...commandArgs,
  ], { cwd: ROOT, encoding: 'utf8' });
}

function fixture() {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'leon-client-success-'));
  const paths = {
    directory,
    slots: path.join(directory, 'case-study-slots.json'),
    state: path.join(directory, 'client-success.json'),
    queue: path.join(directory, 'client-success-queue.json'),
  };
  fs.copyFileSync(SLOTS, paths.slots);
  fs.copyFileSync(STATE, paths.state);
  fs.copyFileSync(QUEUE, paths.queue);
  return paths;
}

test('three empty case-study slots expose evidence, screenshot, and exact approval fields', () => {
  const document = readJson(SLOTS);
  assert.equal(document.schema_version, 1);
  assert.equal(document.slots.length, 3);
  assert.equal(new Set(document.slots.map((slot) => slot.slot_id)).size, 3);

  for (const slot of document.slots) {
    assert.equal(slot.status, 'EMPTY');
    assert.deepEqual(Object.keys(slot.before).sort(), ['evidence_paths', 'fact', 'observed_at']);
    assert.deepEqual(Object.keys(slot.after).sort(), ['evidence_paths', 'fact', 'observed_at']);
    assert.equal(slot.screenshots.length, 2);
    assert.ok(slot.screenshots.every((shot) => Object.hasOwn(shot, 'permission_evidence_path')));
    assert.equal(slot.approval.status, 'NOT_REQUESTED');
    assert.deepEqual(
      Object.keys(slot.approval.draft_publication).sort(),
      Object.keys(slot.approval.approved_publication).sort(),
    );
    assert.equal(slot.approval.packet_sha256, '');
  }
});

test('default files validate and the implementation has no delivery client', () => {
  const result = run({ slots: SLOTS, state: STATE, queue: QUEUE }, ['check']);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /queue is draft-only/i);

  const source = fs.readFileSync(TOOL, 'utf8');
  assert.doesNotMatch(
    source,
    /^\s*(?:from|import)\s+(?:smtplib|requests|httpx|sendgrid|resend|twilio)\b/im,
  );
  assert.doesNotMatch(source, /add_parser\(["']send/i);
});

test('init creates only empty ignored runtime state and never overwrites it', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'leon-client-success-init-'));
  const paths = {
    directory,
    slots: path.join(directory, 'case-study-slots.json'),
    state: path.join(directory, 'client-success.json'),
    queue: path.join(directory, 'client-success-queue.json'),
  };
  fs.copyFileSync(SLOTS, paths.slots);

  let result = run(paths, ['init']);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.deepEqual(readJson(paths.state), { schema_version: 1, projects: [] });
  assert.deepEqual(readJson(paths.queue), { schema_version: 1, items: [] });

  const stateBefore = fs.readFileSync(paths.state, 'utf8');
  const queueBefore = fs.readFileSync(paths.queue, 'utf8');
  result = run(paths, ['init']);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.equal(fs.readFileSync(paths.state, 'utf8'), stateBefore);
  assert.equal(fs.readFileSync(paths.queue, 'utf8'), queueBefore);
});

test('evidenced completion queues exactly two review drafts and one referral draft, never sends', () => {
  const paths = fixture();
  const testimonialBefore = sha256(fs.readFileSync(TESTIMONIAL_DRAFTS));
  const evidence = path.join(paths.directory, 'completion.txt');
  fs.writeFileSync(evidence, 'Test fixture: completion was explicitly recorded.\n');

  let result = run(paths, [
    'add-project',
    '--project-id', 'fixture-project',
    '--project-label', 'Fixture project',
    '--client-first-name', 'Test Client',
    '--contact-ref', 'PRIVATE-FIXTURE-REF',
  ]);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.equal(readJson(paths.queue).items.length, 0, 'active work must not trigger requests');

  result = run(paths, [
    'complete-project',
    '--project-id', 'fixture-project',
    '--completed-at', '2026-08-23',
    '--completion-evidence', evidence,
  ]);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /3 local drafts queued.*0 sent/i);

  let items = readJson(paths.queue).items;
  assert.equal(items.length, 3);
  assert.deepEqual(
    items.map((item) => item.kind).sort(),
    ['GOOGLE_REVIEW_REQUEST', 'LINKEDIN_RECOMMENDATION_REQUEST', 'REFERRAL_REQUEST'],
  );
  assert.equal(items.filter((item) => item.kind === 'REFERRAL_REQUEST').length, 1);
  for (const item of items) {
    assert.equal(item.delivery_mode, 'DRAFT_ONLY');
    assert.equal(item.manual_review_required, true);
    assert.equal(item.incentive_attached, false);
    assert.equal(item.send_authorized, false);
    assert.equal(item.sent_at, '');
  }
  assert.equal(
    items.filter((item) => item.status === 'BLOCKED_MISSING_VERIFIED_URL').length,
    2,
    'review drafts fail closed until exact URLs are supplied',
  );
  assert.equal(items.find((item) => item.kind === 'REFERRAL_REQUEST').status, 'DRAFT_READY_FOR_MANUAL_REVIEW');
  assert.doesNotMatch(items.map((item) => item.draft_body).join('\n'), /https:\/\//i);
  assert.doesNotMatch(
    items.map((item) => item.draft_body).join('\n'),
    /discount|incentive|gift|credit|coupon|compensation|refund/i,
  );

  result = run(paths, [
    'complete-project',
    '--project-id', 'fixture-project',
    '--completed-at', '2026-08-23',
    '--completion-evidence', evidence,
  ]);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  items = readJson(paths.queue).items;
  assert.equal(items.length, 3, 'completion trigger is idempotent');

  result = run(paths, [
    'set-review-links',
    '--project-id', 'fixture-project',
    '--google-review-url', 'https://example.com/not-a-review-link',
  ]);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /verified Google/i);

  result = run(paths, ['check']);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.equal(sha256(fs.readFileSync(TESTIMONIAL_DRAFTS)), testimonialBefore);
});

test('case-study publication fails closed unless the approved package is byte-for-byte exact and evidenced', () => {
  const paths = fixture();
  const beforeEvidence = path.join(paths.directory, 'before.txt');
  const afterEvidence = path.join(paths.directory, 'after.txt');
  const screenshot = path.join(paths.directory, 'result.png');
  const screenshotPermission = path.join(paths.directory, 'screenshot-permission.txt');
  const approvalEvidence = path.join(paths.directory, 'client-approval.txt');
  for (const file of [beforeEvidence, afterEvidence, screenshot, screenshotPermission, approvalEvidence]) {
    fs.writeFileSync(file, `Test fixture evidence for ${path.basename(file)}\n`);
  }

  const document = readJson(paths.slots);
  const slot = document.slots[0];
  slot.status = 'APPROVED';
  slot.project_id = 'fixture-case-study';
  slot.project_label = 'Fixture case study';
  slot.client_display_label = 'Approved fixture client label';
  slot.before = {
    fact: 'Test fixture before fact.',
    observed_at: '2026-08-01',
    evidence_paths: [beforeEvidence],
  };
  slot.after = {
    fact: 'Test fixture after fact.',
    observed_at: '2026-08-23',
    evidence_paths: [afterEvidence],
  };
  slot.metrics = [];
  slot.screenshots = [{
    stage: 'result',
    path: screenshot,
    caption: 'Test fixture result screen.',
    captured_at: '2026-08-23',
    permission_evidence_path: screenshotPermission,
  }];
  slot.approval.status = 'APPROVED';
  slot.approval.draft_publication = {
    title: 'Fixture case study',
    before_fact: slot.before.fact,
    after_fact: slot.after.fact,
    quote: 'Test fixture quote.',
    attribution: 'Approved fixture attribution',
    rating: '',
    screenshot_paths: [screenshot],
    placement: 'leonbuilds.org and related project marketing',
  };
  slot.approval.approved_publication = {
    ...slot.approval.draft_publication,
    quote: 'Changed without exact approval.',
  };
  slot.approval.approved_at = '2026-08-23';
  slot.approval.approval_evidence_path = approvalEvidence;
  slot.approval.rating_evidence_path = '';
  slot.approval.packet_sha256 = publicationDigest(slot.approval.draft_publication);
  fs.writeFileSync(paths.slots, `${JSON.stringify(document, null, 2)}\n`);

  let result = run(paths, ['check']);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /approved publication must exactly equal/i);

  slot.approval.approved_publication = { ...slot.approval.draft_publication };
  fs.writeFileSync(paths.slots, `${JSON.stringify(document, null, 2)}\n`);
  result = run(paths, ['check']);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /1 publication-ready/i);
});
