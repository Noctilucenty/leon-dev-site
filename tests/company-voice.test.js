'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const ROOT = path.join(__dirname, '..');
const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');
const text = html => html.replace(/<script\b[\s\S]*?<\/script>/gi, '')
  .replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

test('company voice keeps a named founder instead of implying an anonymous team', () => {
  for (const file of ['index.html', 'technical-build-partner.html']) {
    const visible = text(read(file));
    assert.match(visible, /Founder-led delivery/i, file);
    assert.match(visible, /Leon Kelvin Li/, file);
    assert.doesNotMatch(visible, /our team of (?:developers|engineers|experts)/i, file);
  }
  assert.match(text(read('quote.html')), /Tell us what is broken, manual, or missing/i);
  assert.match(text(read('quote.html')), /Your request was saved\. Leon will reply/i);
});

test('AI offers explain limits without promising perfect answers or availability', () => {
  const chatbot = text(read('services/ai-chatbots.html'));
  assert.match(chatbot, /help customers get answers from your business information/i);
  assert.match(chatbot, /ai can still make mistakes/i);
  assert.match(chatbot, /health-education prototype/i);
  assert.match(chatbot, /project assistant on this website is a separate build/i);
  assert.doesNotMatch(chatbot, /without inventing prices|no invented prices|the moment it should/i);
  const phone = text(read('services/ai-phone-agents.html'));
  assert.match(phone, /ai can make mistakes/i);
  assert.match(phone, /fallback when the service is unavailable/i);
  assert.doesNotMatch(phone, /every call, immediately|instant transfer to staff on anything unusual/i);
});

test('localized homepages distinguish the human from AI and label the demo honestly', () => {
  const cases = [
    ['pt/index.html', /Leon fala português/, /assistente com IA/, /carrinho de demonstração; pagamentos e cozinha ainda não estão ativos/],
    ['es/index.html', /Leon habla español/, /asistente con IA/, /carrito de demostración; pagos y cocina no están activos/],
    ['zh/index.html', /Leon 会说中文/, /AI 助手/, /演示购物车；支付与厨房流程尚未上线/],
  ];
  for (const [file, human, ai, demo] of cases) {
    const visible = text(read(file));
    assert.match(visible, human, file);
    assert.match(visible, ai, file);
    assert.match(visible, demo, file);
  }
  assert.match(text(read('pt/automacao.html')), /IA pode errar/);
  assert.match(text(read('es/automatizacion.html')), /la IA puede equivocarse/);
  assert.match(text(read('zh/zidonghua.html')), /AI 仍然可能答错/);
});
