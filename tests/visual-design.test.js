'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const read = file => fs.readFileSync(path.join(__dirname, '..', file), 'utf8');

test('all canonical subpages share the homepage-derived local design layer', () => {
  const urls = [...read('sitemap.xml').matchAll(/<loc>https:\/\/leonbuilds.org([^<]*)<\/loc>/g)].map(x => x[1]);
  assert.equal(urls.length, 50);
  for (const url of urls.filter(x => x !== '/')) {
    const file = url.endsWith('/') ? url.slice(1) + 'index.html' : ['es','pt','zh'].includes(url.slice(1)) ? url.slice(1) + '/index.html' : url.slice(1) + '.html';
    const html = read(file);
    assert.equal((html.match(/href="\/site-design.css"/g) || []).length, 1, file);
    assert.equal((html.match(/src="\/site-motion.js" defer/g) || []).length, 1, file);
    assert.match(html, /name="color-scheme" content="light"/, file);
    assert.doesNotMatch(html, /fonts\.googleapis\.com/, file);
  }
  assert.doesNotMatch(read('homepage/index.html'), /site-motion\.js/);
  for (const font of ['lb-geist','lb-serif','lb-serif-italic']) {
    assert.ok(fs.statSync(path.join(__dirname,'..','assets/fonts',font+'.woff2')).size > 1000);
  }
});

test('guide teaches three distinct choices before optional source-backed detail', () => {
  const html = read('guides/website-builder-or-custom-software.html');
  const beforeDetails = html.split('<details class="rail visual-details"')[0];
  for (const name of ['Website','Automation','Custom software']) assert.ok(beforeDetails.includes(name));
  assert.equal((html.match(/type="radio" name="build-choice"/g) || []).length, 3);
  assert.equal((html.match(/data-flow-play hidden/g) || []).length, 3);
  assert.match(beforeDetails, /You do not need all three at once/);
  assert.match(beforeDetails, /Human approval/);
  assert.match(beforeDetails, /Leon Builds sells implementation services/);
  assert.match(html, /mini-gallery/);
  assert.match(html, /mini-inbox/);
  assert.match(html, /mini-rule/);
  assert.match(html, /mini-person/);
  assert.match(html, /Read the full guide &amp; quote checklist|Read the full guide & quote checklist/);
  assert.ok(html.indexOf('are simulations') > html.indexOf('</details>'), 'proof limitation stays outside the closed guide');
  assert.match(html, /id="scope-checklist"/);
});

test('English and localized service visuals retain scope and non-submission labels', () => {
  for (const file of ['services/websites.html','services/ai-chatbots.html','industries/contractors.html',
    'es/pagina-web.html','pt/criar-site.html','zh/zuo-wangzhan.html']) {
    const html = read(file);
    assert.match(html, /class="flow-scene"/, file);
    assert.match(html, /class="rail visual-details"/, file);
    assert.match(html, /data-flow-play hidden/, file);
  }
  assert.match(read('services/ai-chatbots.html'), /AI can make mistakes/);
  assert.match(read('services/mobile-apps.html'), /does not guarantee approval/);
  assert.match(read('industries/healthcare.html'), /not medical advice or a compliance guarantee/);
  assert.match(read('es/pagina-web.html'), /No se envía nada/);
  assert.match(read('pt/criar-site.html'), /Nada é enviado/);
  assert.match(read('zh/zuo-wangzhan.html'), /不会发送任何信息/);
});

test('motion stays progressive, bounded, accessible and independent of forms', () => {
  const css = read('site-design.css');
  const js = read('site-motion.js');
  assert.match(css, /\.flow-play\[hidden\]\s*\{\s*display:none/);
  assert.match(css, /\.choice-panel\[hidden\]\s*\{\s*display:none/);
  assert.match(css, /input:focus-visible \+ span/);
  assert.match(css, /@supports selector\(:has\(\*\)\)/);
  assert.match(css, /prefers-reduced-motion:reduce/);
  assert.match(css, /overflow-wrap:anywhere/);
  assert.match(css, /\.as-input,\.as-in\s*\{[^}]*16px/);
  assert.doesNotMatch(js, /\bfetch\s*\(|XMLHttpRequest|\.submit\s*\(|setInterval\s*\(/);
  assert.match(js, /closest\('form,\.call-page,\.quote-page,\.as-panel'\)/);
  assert.match(js, /3200/);
  assert.match(js, /parent\.tagName==='DETAILS'/);
});

function flowHarness(reduced = false) {
  const button = {hidden:true, addEventListener(name, fn) {this[name] = fn;}};
  const feedback = {textContent:'', dataset:{complete:'Example complete'}};
  const classes = new Set();
  const scene = {offsetWidth:100, classList:{add:x=>classes.add(x),remove:x=>classes.delete(x)},
    querySelector:s=>s.includes('feedback')?feedback:button, closest:()=>null};
  const events = {};
  const media = {matches:reduced, addEventListener:(_,fn)=>{events.reduce=fn;}};
  const doc = {hidden:false, querySelectorAll:s=>s==='[data-flow]'?[scene]:[],
    addEventListener:(n,fn)=>{(events[n] ||= []).push(fn);}};
  const timers = new Map(); let next = 0; const observers=[];
  const window = {matchMedia:()=>media, IntersectionObserver:true,addEventListener:()=>{}};
  class Observer {constructor(fn){this.fn=fn;this.disconnected=false;observers.push(this);}observe(){}unobserve(){}disconnect(){this.disconnected=true;}}
  const context = {window,document:doc,Map,Array,location:{hash:''},IntersectionObserver:Observer,
    setTimeout:fn=>{timers.set(++next,fn);return next;},clearTimeout:id=>timers.delete(id)};
  vm.runInNewContext(read('site-motion.js').split('/* Short, replayable examples.')[1].split('*/').slice(1).join('*/'), context);
  return {button,feedback,classes,events,media,doc,timers,observers,scene};
}

test('replay is enabled only after initialization and stops after one bounded example', () => {
  const h=flowHarness(); assert.equal(h.button.hidden,false);
  h.button.click(); assert.ok(h.classes.has('is-playing')); assert.equal(h.timers.size,1);
  [...h.timers.values()][0]();
  assert.equal(h.classes.size,0); assert.equal(h.timers.size,0); assert.equal(h.feedback.textContent,'Example complete');
});

test('reduced motion gives static feedback; tab hiding clears timers but not unseen scenes', () => {
  const reduced=flowHarness(true); reduced.button.click();
  assert.equal(reduced.classes.size,0); assert.equal(reduced.timers.size,0);
  assert.equal(reduced.feedback.textContent,'Example complete');
  const h=flowHarness(); h.button.click(); h.doc.hidden=true;
  h.events.visibilitychange.forEach(fn=>fn()); assert.equal(h.timers.size,0);
  assert.equal(h.observers[0].disconnected,false);
  h.observers[0].fn([{isIntersecting:true,target:h.scene}]); assert.equal(h.timers.size,0);
  h.doc.hidden=false; h.observers[0].fn([{isIntersecting:true,target:h.scene}]); assert.equal(h.timers.size,1);
  h.media.matches=true; h.events.reduce(); assert.equal(h.timers.size,0);
});
