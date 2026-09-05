'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');

test('assistant has a deterministic one-time handoff independent of model wording', () => {
  const source = read('assist.js');
  assert.match(source, /function readyForHandoff\(\)/);
  assert.match(source, /chars >= 80 \|\| \(userText\.length >= 2 && chars >= 24\)/);
  assert.match(source, /data-as-convert-go/);
  assert.match(source, /chat_handoff_offer_shown/);
  assert.match(source, /chat_handoff_offer_click/);
  assert.match(source, /chat_handoff_offer_dismissed/);
  assert.match(source, /handoffOffered: state\.leadOfferShown \|\| state\.leadSubmitted/);
  assert.match(source, /affirmativeIntent\(text\)/);
  assert.match(source, /catch\(function \(err\)[\s\S]*?state\.leadOfferShown = true;[\s\S]*?renderConversionOffer\(\);/, 'a failed AI reply still offers the human handoff');
});

test('handoff action and success state are localized in all supported languages', () => {
  const source = read('assist.js');
  for (const phrase of [
    'Send this project to Leon',
    'Enviar este proyecto a Leon',
    'Enviar este projeto ao Leon',
    '把这个项目发送给 Leon',
    'Project sent to Leon',
    'Proyecto enviado a Leon',
    'Projeto enviado ao Leon',
    '项目已发送给 Leon'
  ]) assert.ok(source.includes(phrase), phrase);
});

test('assistant success is persistent, accessible, and blocks duplicate submission', () => {
  const source = read('assist.js');
  assert.match(source, /leadSubmitted: state\.leadSubmitted/);
  assert.match(source, /leadSuccessDismissed: state\.leadSuccessDismissed/);
  assert.match(source, /leadReceipt: state\.leadReceipt/);
  assert.match(source, /role="region" aria-labelledby="as-success-title" tabindex="-1"/);
  assert.match(source, /class="as-success-kicker" role="status" aria-live="assertive" aria-atomic="true"/);
  assert.match(source, /if \(state\.leadSubmitted\) \{\s*showLeadSuccess\(state\.leadReceipt, true\);\s*return;/);
  assert.match(source, /showLeadSuccess\(receipt, true\)/);
  assert.match(source, /successView\.focus/);
  assert.match(source, /state\.firstSent = state\.history\.some/, 'restored history must not emit a second first-message event');
  assert.match(source, /idempotencyKey: state\.leadIdempotencyKey/);
  assert.match(source, /leadIdempotencyKey: state\.leadIdempotencyKey/);
  assert.match(source, /return postLead\(payload, true\)/, 'a retry must keep the exact idempotent payload');
  assert.doesNotMatch(source, /k !== 'conversationSummary'/, 'a retry must not change the fingerprinted payload');
  assert.match(source, /recentUser\.join\('\\n'\)/, 'the project field uses recent visitor context, not only the first starter');
  assert.doesNotMatch(source, /successBody:\s*['"][^'"]*Leon (?:has )?read/i);
});

test('assistant conversion controls meet the mobile visibility floor', () => {
  const css = read('assist.css');
  assert.match(css, /\.as-hbtn\{[\s\S]*?min-height:44px/);
  assert.match(css, /\.as-hbtn-lead\{[\s\S]*?background:var\(--ac/);
  assert.match(css, /\.as-convert\{[\s\S]*?border:2px solid var\(--ac/);
  assert.match(css, /\.as-convert button\{[\s\S]*?min-height:48px/);
  assert.match(css, /\.as-success\{[\s\S]*?border:2px solid var\(--ac/);
  assert.match(css, /\.as-success > p:not[\s\S]*?font-size:16px/);
  assert.match(css, /prefers-reduced-motion:reduce[\s\S]*?\.as-convert\{ animation:none; \}/);
});

test('regular quote form uses the same unmistakable transaction state', () => {
  const source = read('tools/build_pages.py');
  const css = read('styles.css');
  assert.match(source, /class="qok"[^>]*role="region"[^>]*aria-labelledby="qok-title"/);
  assert.match(source, /class="label" role="status" aria-live="assertive" aria-atomic="true"/);
  assert.match(source, /d\.idempotencyKey=submissionKey/);
  assert.match(source, /Your project was <em>sent to Leon Builds\.<\/em>/);
  assert.match(source, /Your request was saved\. Leon will reply to the email you provided/);
  assert.match(css, /\.qform\[hidden\]\{ display:none; \}/, 'the form must actually disappear after a successful submit');
  assert.match(css, /\.qok\{[\s\S]*?border:2px solid var\(--ac\)/);
  assert.match(css, /\.qok \.sub\{[\s\S]*?font-size:16px/);
});
