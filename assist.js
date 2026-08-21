/* leon --assist · the site's floating project assistant + event/utm plumbing.
   Same discipline as app.js: everything in guarded blocks, content never depends
   on this file. No frameworks, no keys — the browser only ever talks to our own
   backend (see server/), never to OpenAI directly.

   The ONE deploy-time constant: API_BASE. After creating the Render service,
   if its URL differs from https://leon-assist.onrender.com, change it here. */

(function () {
  'use strict';

  var API_BASE = (window.LEON_ASSIST && window.LEON_ASSIST.api) ||
    (/^(localhost|127\.0\.0\.1)$/.test(location.hostname)
      ? 'http://localhost:8787'
      : 'https://leon-assist.onrender.com');

  var run = function (fn) { try { fn(); } catch (e) { /* fail soft */ } };
  var $ = function (s, r) { return (r || document).querySelector(s); };

  /* ══ utm + first-touch capture ═══════════════════════════ */
  var attribution = {};
  run(function () {
    var KEY = 'leon_attr';
    try {
      var saved = JSON.parse(localStorage.getItem(KEY) || 'null');
      var qs = new URLSearchParams(location.search);
      var tag = qs.get('utm_source') || qs.get('s') || '';
      if (!saved) {
        saved = {
          firstPage: location.pathname,
          referrer: (document.referrer || '').slice(0, 200),
          utmSource: tag,
          utmMedium: qs.get('utm_medium') || '',
          utmCampaign: qs.get('utm_campaign') || ''
        };
        localStorage.setItem(KEY, JSON.stringify(saved));
      } else if (tag) {
        saved.utmSource = tag;
        saved.utmMedium = qs.get('utm_medium') || saved.utmMedium;
        saved.utmCampaign = qs.get('utm_campaign') || saved.utmCampaign;
        localStorage.setItem(KEY, JSON.stringify(saved));
      }
      attribution = saved;
    } catch (e) {}
  });

  /* ══ event beacon (first-party, log-only) ════════════════ */
  function evt(name) {
    try {
      var body = JSON.stringify({
        name: name, path: location.pathname,
        ref: (document.referrer || attribution.referrer || '').slice(0, 200),
        utm: attribution.utmSource || ''
      });
      if (navigator.sendBeacon) {
        navigator.sendBeacon(API_BASE + '/api/event', new Blob([body], { type: 'application/json' }));
      } else {
        fetch(API_BASE + '/api/event', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body, keepalive: true }).catch(function () {});
      }
    } catch (e) {}
  }
  window.leonEvt = evt;

  // one page_view per load — this is what the /api/traffic sources table counts
  run(function () { evt('page_view'); });

  // declarative events: any element with data-evt fires on click
  run(function () {
    document.addEventListener('click', function (e) {
      var el = e.target && e.target.closest && e.target.closest('[data-evt]');
      if (el) evt(el.getAttribute('data-evt'));
    }, { passive: true });
  });

  /* ══ language ════════════════════════════════════════════
     Three places care: which page we send them to, which starters we
     show, and which language the assistant answers in. One stored
     choice drives all three. We only ask when the browser says they
     read something other than the page they landed on. */
  var LANG_KEY = 'leon_lang';
  var PAGE_LANG = ((document.documentElement.getAttribute('lang') || 'en').slice(0, 2)).toLowerCase();
  var LANG_PAGE = { en: '/', pt: '/pt', zh: '/zh', es: '/es' };
  var LANG_NAME = { en: 'english', pt: 'português', zh: '中文', es: 'español' };
  var LANG_ASK = 'what language do you prefer? · qual idioma? · 用什么语言？';
  var LANG_SWITCH = {
    es: 'esta página también existe en español',
    pt: 'esta página também existe em português',
    zh: '这个页面也有中文版',
    en: 'this page is also in english'
  };

  function storedLang() {
    try { return localStorage.getItem(LANG_KEY) || ''; } catch (e) { return ''; }
  }
  function setLang(v) {
    try { localStorage.setItem(LANG_KEY, v); } catch (e) {}
  }
  function detectLang() {
    var list = navigator.languages || [navigator.language || ''];
    for (var i = 0; i < list.length; i++) {
      var t = String(list[i] || '').toLowerCase();
      if (t.indexOf('pt') === 0) return 'pt';
      if (t.indexOf('zh') === 0) return 'zh';
      if (t.indexOf('es') === 0) return 'es';
      if (t.indexOf('en') === 0) return 'en';
    }
    return '';
  }
  // keep ?s= / utm attribution across a language switch
  function langHref(v) {
    return (LANG_PAGE[v] || '/') + (location.search || '');
  }

  /* the page-level nudge — only when the browser disagrees with the page */
  var langBar = null;
  run(function () {
    if (storedLang()) return;
    // Already on a translated page? They picked by clicking the ad that sent
    // them here. Asking again at the door is friction — most Brazilians and
    // Chinese speakers in the US carry english-set phones, so locale sniffing
    // would prompt literally everyone. The chat still offers the choice.
    if (PAGE_LANG !== 'en') return;
    var want = detectLang();
    var target = want;
    if (!target || target === PAGE_LANG) return;
    try { if (sessionStorage.getItem('leon_lang_dismissed')) return; } catch (e) {}

    var bar = document.createElement('div');
    bar.className = 'as-langbar';
    bar.setAttribute('role', 'dialog');
    bar.setAttribute('aria-label', 'language');
    bar.style.position = 'fixed';
    bar.innerHTML = '<button class="x" type="button" aria-label="close">✕</button>'
      + '<p>' + LANG_ASK + '</p><div class="opts"></div>';
    var opts = bar.querySelector('.opts');

    ['en', 'es', 'pt', 'zh'].forEach(function (v) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = LANG_NAME[v];
      if (v === target) b.className = 'go';
      b.addEventListener('click', function () {
        setLang(v);
        evt('lang_pick_' + v);
        if (v === PAGE_LANG) { bar.remove(); return; }
        location.href = langHref(v);
      });
      opts.appendChild(b);
    });
    bar.querySelector('.x').addEventListener('click', function () {
      try { sessionStorage.setItem('leon_lang_dismissed', '1'); } catch (e) {}
      bar.remove();
    });
    document.body.appendChild(bar);
    langBar = bar;
    evt('lang_prompt_shown');
  });

  /* ══ language switcher, in the nav of every page ═════════
     Always visible, not just when we guess the visitor needs it. Pages that
     have no translation yet send the visitor to that language's home page
     rather than a dead end, and ?s= attribution rides along. */
  var LANG_SHORT = { en: 'en', es: 'es', pt: 'pt', zh: '中文' };
  run(function () {
    var nav = $('.nav-end');
    if (!nav) return;
    var cur = storedLang() || PAGE_LANG;
    var wrap = document.createElement('div');
    wrap.className = 'as-langpick';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'language');
    ['en', 'es', 'pt', 'zh'].forEach(function (v) {
      var a = document.createElement('a');
      a.href = langHref(v);
      a.textContent = LANG_SHORT[v];
      a.setAttribute('lang', v);
      a.title = LANG_NAME[v];
      if (v === cur) a.className = 'on';
      a.addEventListener('click', function () {
        setLang(v);
        evt('lang_switch_' + v);
      });
      wrap.appendChild(a);
    });
    nav.insertBefore(wrap, nav.firstChild);
  });

  /* ══ contextual starter prompts ══════════════════════════ */
  var STARTERS_L = {
    pt: [
      'ainda anoto tudo no papel — dá pra melhorar?',
      'quero que o cliente peça pelo site',
      'quanto custa um site pro meu negócio?'
    ],
    zh: [
      '现在还靠本子和微信记单，能改吗？',
      '我想让客人自己在网上下单',
      '做一个店里的网站要多少钱？'
    ],
    es: [
      'todavía anoto todo a mano — ¿se puede mejorar?',
      'quiero que el cliente pida por internet',
      '¿cuánto cuesta una página para mi negocio?'
    ]
  };
  function starters() {
    var pref = storedLang() || PAGE_LANG;
    if (STARTERS_L[pref]) return STARTERS_L[pref];
    var p = location.pathname;
    if (p.indexOf('/industries/restaurants') === 0) return [
      'nobody answers our phone during a rush',
      'i want customers to order online',
      'what would this cost for one location?'
    ];
    if (p.indexOf('/industries/') === 0) return [
      'here is what my business does…',
      'what would you automate first?',
      'what does something like this cost?'
    ];
    if (p.indexOf('/services/ai-') === 0 || p.indexOf('/services/business-automation') === 0) return [
      'what repetitive work can actually be automated?',
      'my team retypes things between systems',
      'is ai even worth it at my size?'
    ];
    if (p.indexOf('/services/mobile-apps') === 0) return [
      'i have an app idea but no technical team',
      'what does an app cost to build?',
      'ios first or both platforms?'
    ];
    if (p.indexOf('/services/') === 0) return [
      'what does this usually cost?',
      'how long would this take?',
      'here is my situation…'
    ];
    if (p.indexOf('/quote') === 0) return [
      'help me describe my project',
      'i am not sure what i need'
    ];
    return [
      'i need a website',
      'i want to automate something',
      'i have an app idea',
      'can ai actually help my business?',
      "i don't know what i need"
    ];
  }

  /* ══ the widget ══════════════════════════════════════════ */
  run(function () {
    if (window.__leonAssist) return;
    window.__leonAssist = true;

    var SS = 'leon_chat';
    var state = { open: false, busy: false, history: [], sessionId: '', warmed: false, firstSent: false };

    try {
      var saved = JSON.parse(sessionStorage.getItem(SS) || 'null');
      if (saved && Array.isArray(saved.history)) { state.history = saved.history; state.sessionId = saved.sessionId || ''; }
    } catch (e) {}
    if (!state.sessionId) {
      state.sessionId = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
    }
    function save() {
      try { sessionStorage.setItem(SS, JSON.stringify({ history: state.history.slice(-60), sessionId: state.sessionId })); } catch (e) {}
    }

    /* dom */
    var launch = document.createElement('button');
    launch.className = 'as-launch';
    launch.type = 'button';
    launch.setAttribute('aria-haspopup', 'dialog');
    launch.innerHTML = '<i>[&gt;_]</i> ask about your project';

    var panel = document.createElement('section');
    panel.className = 'as-panel';
    panel.hidden = true;
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'true');
    panel.setAttribute('aria-label', "leon's ai project assistant");
    panel.innerHTML =
      '<header class="as-head">' +
        '<span class="dot">[<span aria-hidden="true">•</span>]</span>' +
        '<div><h2>leon --assist</h2><div class="st" data-as-status>ai project assistant</div></div>' +
        '<span class="sp"></span>' +
        '<button class="as-hbtn" type="button" data-as-lead-open>send to leon</button>' +
        '<button class="as-hbtn" type="button" data-as-new title="start over">new</button>' +
        '<button class="as-hbtn" type="button" data-as-close aria-label="close chat">✕</button>' +
      '</header>' +
      '<div class="as-log" data-as-log aria-live="polite"></div>' +
      '<div class="as-lang" data-as-lang hidden><p></p><div class="opts"></div></div>' +
      '<div class="as-starts" data-as-starts></div>' +
      '<form class="as-lead" data-as-lead hidden>' +
        '<p><b>send this conversation to leon.</b> your email app opens with it already written — you just hit send. he replies himself, usually same day.</p>' +
        '<input name="name" type="text" placeholder="name" autocomplete="name">' +
        '<div class="row2">' +
          '<input name="email" type="email" placeholder="email (required)" autocomplete="email" required>' +
          '<input name="phone" type="tel" placeholder="phone (optional)" autocomplete="tel">' +
        '</div>' +
        '<input name="website" type="text" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">' +
        '<p class="as-err" data-as-err></p>' +
        '<div class="acts"><button class="go" type="submit">write the email</button><button class="no" type="button" data-as-lead-close>not yet</button></div>' +
      '</form>' +
      '<footer class="as-foot">' +
        '<div class="as-inrow">' +
          '<textarea class="as-in" data-as-in rows="1" placeholder="describe your business or your problem…" aria-label="message"></textarea>' +
          '<button class="as-send" data-as-send type="button" aria-label="send">↵</button>' +
        '</div>' +
        '<p class="as-note">ai assistant — may process messages to answer and scope your project. no passwords or payment details. ' +
          'prefer a human? <a href="mailto:leondragon3798@gmail.com">email</a> · <a href="tel:+15108267735">call</a></p>' +
      '</footer>';

    document.body.appendChild(launch);
    document.body.appendChild(panel);

    var log = $('[data-as-log]', panel);
    var startsBox = $('[data-as-starts]', panel);
    var input = $('[data-as-in]', panel);
    var sendBtn = $('[data-as-send]', panel);
    var statusEl = $('[data-as-status]', panel);
    var leadForm = $('[data-as-lead]', panel);
    var leadErr = $('[data-as-err]', panel);
    var lastFocus = null;

    function msgEl(role, text) {
      var d = document.createElement('div');
      d.className = 'as-msg ' + (role === 'user' ? 'u' : role === 'sys' ? 'sys' : 'a');
      d.textContent = text;
      log.appendChild(d);
      log.scrollTop = log.scrollHeight;
      return d;
    }
    function renderHistory() {
      log.innerHTML = '';
      if (!state.history.length) {
        msgEl('assistant', "tell me what your business does and what part of the week is still done by hand — i'll tell you what software could take off your plate, what it roughly starts at, and just as readily when you don't need me.");
      }
      state.history.forEach(function (m) { msgEl(m.role, m.content); });
      renderStarters();
      renderLangChoice();
    }
    function renderStarters() {
      startsBox.innerHTML = '';
      if (state.history.length) return;
      starters().forEach(function (s) {
        var b = document.createElement('button');
        b.type = 'button'; b.textContent = s;
        b.addEventListener('click', function () { send(s); });
        startsBox.appendChild(b);
      });
    }

    /* asked once, at the top of the first conversation, so the reply comes
       back in their language instead of making them ask for it */
    function renderLangChoice() {
      var box = $('[data-as-lang]', panel);
      if (!box) return;
      if (storedLang() || state.history.length) { box.hidden = true; return; }
      box.hidden = false;
      box.querySelector('p').textContent = LANG_ASK;
      var opts = box.querySelector('.opts');
      opts.innerHTML = '';
      ['en', 'pt', 'zh', 'es'].forEach(function (v) {
        var b = document.createElement('button');
        b.type = 'button'; b.textContent = LANG_NAME[v];
        b.addEventListener('click', function () {
          setLang(v);
          evt('lang_pick_' + v);
          box.hidden = true;
          renderStarters();
          // a page in their language exists — offer it, don't force it
          if (LANG_PAGE[v] && v !== PAGE_LANG) {
            var d = msgEl('assistant', '');
            d.innerHTML = LANG_SWITCH[v] + ' — <a href="' + langHref(v) + '">'
              + LANG_PAGE[v] + '</a>';
          }
        });
        opts.appendChild(b);
      });
    }

    function warm() {
      if (state.warmed) return;
      state.warmed = true;
      fetch(API_BASE + '/api/health', { method: 'GET' }).catch(function () { state.warmed = false; });
    }

    function open(starter) {
      lastFocus = document.activeElement;
      panel.hidden = false; launch.hidden = true;
      state.open = true;
      if (window.matchMedia('(max-width:640px)').matches) document.documentElement.style.overflow = 'hidden';
      renderHistory();
      warm();
      if (langBar) { langBar.remove(); langBar = null; }
      evt('chat_open');
      setTimeout(function () { input.focus(); }, 60);
      if (starter) send(starter);
    }
    function close() {
      panel.hidden = true; launch.hidden = false;
      state.open = false;
      document.documentElement.style.overflow = '';
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function setBusy(b) {
      state.busy = b;
      sendBtn.disabled = b;
      statusEl.textContent = b ? 'thinking…' : 'ai project assistant';
    }

    function send(text) {
      text = (text || input.value || '').trim();
      if (!text || state.busy) return;
      input.value = ''; input.style.height = '';
      startsBox.innerHTML = '';
      var lbox = $('[data-as-lang]', panel); if (lbox) lbox.hidden = true;
      if (!state.firstSent) { state.firstSent = true; evt('chat_first_message'); }

      state.history.push({ role: 'user', content: text });
      msgEl('user', text);
      save();
      setBusy(true);

      var think = document.createElement('div');
      think.className = 'as-think';
      think.innerHTML = 'thinking <i>▌</i>';
      log.appendChild(think); log.scrollTop = log.scrollHeight;

      var slowNote = setTimeout(function () {
        think.innerHTML = 'waking the assistant — free hosting naps when idle, can take ~30s <i>▌</i>';
      }, 4500);

      var ctrl = new AbortController();
      var timeout = setTimeout(function () { ctrl.abort(); }, 95000);

      fetch(API_BASE + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: ctrl.signal,
        body: JSON.stringify({
          sessionId: state.sessionId,
          page: location.pathname,
          lang: storedLang() || PAGE_LANG,
          messages: state.history.slice(-40)
        })
      }).then(function (res) {
        clearTimeout(slowNote);
        if (!res.ok) {
          return res.json().catch(function () { return {}; }).then(function (j) {
            throw new Error(j.error || ('assistant unavailable (' + res.status + ')'));
          });
        }
        think.remove();
        var el = msgEl('assistant', '');
        var reader = res.body.getReader();
        var dec = new TextDecoder();
        var acc = '';
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) return acc;
            acc += dec.decode(r.value, { stream: true });
            el.textContent = acc;
            log.scrollTop = log.scrollHeight;
            return pump();
          });
        }
        return pump().then(function (full) {
          state.history.push({ role: 'assistant', content: full });
          save();
        });
      }).catch(function (err) {
        clearTimeout(slowNote);
        think.remove();
        var m = (err && err.name === 'AbortError') ? TIMEOUT_MSG[lang()] || TIMEOUT_MSG.en : (err.message || '');
        msgEl('sys', m);
        // A failed reply must not end the conversation. Give them the channels
        // that always work, as buttons — not an address to copy by hand.
        handoffRow();
      }).finally(function () {
        clearTimeout(timeout);
        setBusy(false);
        input.focus();
      });
    }

    /* ══ handoff: what the panel offers when the model cannot answer ══ */
    var TIMEOUT_MSG = {
      en: 'that took too long. rather than keep you waiting, here is leon directly:',
      pt: 'demorou demais. em vez de te deixar esperando, fala direto com o leon:',
      zh: '太慢了。别等了，直接联系 leon：',
      es: 'tardó demasiado. en vez de hacerte esperar, habla directo con leon:'
    };
    var HANDOFF = {
      en: [['whatsapp', 'https://wa.me/15108267735?text=Hi%20Leon%20-%20saw%20your%20site.%20My%20business%20is%3A%20'], ['call (510) 826-7735', 'tel:+15108267735'], ['email', 'mailto:leondragon3798@gmail.com?subject=project']],
      pt: [['whatsapp', 'https://wa.me/15108267735?text=Oi%20Leon%2C%20vi%20o%20seu%20site.%20Meu%20neg%C3%B3cio%20%C3%A9%3A%20'], ['ligar (510) 826-7735', 'tel:+15108267735'], ['email', 'mailto:leondragon3798@gmail.com?subject=projeto']],
      zh: [['打电话 (510) 826-7735', 'tel:+15108267735'], ['whatsapp', 'https://wa.me/15108267735'], ['发邮件', 'mailto:leondragon3798@gmail.com?subject=项目']],
      es: [['whatsapp', 'https://wa.me/15108267735'], ['llamar (510) 826-7735', 'tel:+15108267735'], ['email', 'mailto:leondragon3798@gmail.com']]
    };
    function lang() { return storedLang() || PAGE_LANG; }
    function handoffRow() {
      var opts = HANDOFF[lang()] || HANDOFF.en;
      var box = document.createElement('div');
      box.className = 'as-starts';
      opts.forEach(function (o) {
        var a = document.createElement('a');
        a.href = o[1];
        a.textContent = o[0];
        if (o[1].indexOf('http') === 0) { a.target = '_blank'; a.rel = 'noopener'; }
        a.addEventListener('click', function () { evt('handoff_' + lang()); });
        box.appendChild(a);
      });
      log.appendChild(box);
      log.scrollTop = log.scrollHeight;
    }

    /* lead form */
    function openLead() {
      leadForm.hidden = false;
      leadErr.textContent = '';
      $('input[name="email"]', leadForm).focus();
    }
    leadForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = new FormData(leadForm);
      var email = String(f.get('email') || '').trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { leadErr.textContent = 'that email does not look right.'; return; }
      leadErr.textContent = '';
      var name = String(f.get('name') || ''), phone = String(f.get('phone') || '');
      // Logged server-side as a backup, but nobody waits on it — the browser
      // hands the conversation straight to their own mail app.
      try {
        fetch(API_BASE + '/api/lead', {
          method: 'POST',
          keepalive: true,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            via: 'chat', name: name, email: email, phone: phone,
            website: String(f.get('website') || ''),
            messages: state.history.slice(-40),
            problem: (state.history.filter(function (m) { return m.role === 'user'; })[0] || {}).content || '',
            sourcePage: location.pathname,
            referrer: attribution.referrer || '',
            utmSource: attribution.utmSource || '',
            utmMedium: attribution.utmMedium || '',
            utmCampaign: attribution.utmCampaign || ''
          })
        }).catch(function () {});
      } catch (e) {}
      var talk = state.history.slice(-20).map(function (m) {
        return (m.role === 'user' ? 'me: ' : 'assistant: ') + String(m.content || '').trim();
      }).join('\n\n');
      var body = 'name: ' + (name || '(not given)') + '\nemail: ' + email + (phone ? '\nphone: ' + phone : '')
        + '\n\nwhat we talked about on the site:\n\n' + talk
        + '\n\n— sent from leonbuilds.org' + (location.pathname !== '/' ? ' (' + location.pathname + ')' : '');
      if (body.length > 1600) body = body.slice(0, 1600) + '\n…';
      var href = 'mailto:leondragon3798@gmail.com?subject=' + encodeURIComponent('project inquiry' + (name ? ' — ' + name : ''))
        + '&body=' + encodeURIComponent(body);
      leadForm.hidden = true;
      evt('lead_submit');
      msgEl('sys', 'your email app is opening with this conversation in it — hit send and it comes straight to leon. if nothing opened, email leondragon3798@gmail.com.');
      window.location.href = href;
    });

    /* wiring */
    launch.addEventListener('click', function () { open(); });
    launch.addEventListener('mouseenter', warm, { once: false });
    panel.addEventListener('click', function (e) {
      if (e.target.closest('[data-as-close]')) close();
      if (e.target.closest('[data-as-lead-open]')) openLead();
      if (e.target.closest('[data-as-lead-close]')) leadForm.hidden = true;
      if (e.target.closest('[data-as-new]')) { state.history = []; save(); leadForm.hidden = true; renderHistory(); }
      if (e.target.closest('[data-as-send]')) send();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
    input.addEventListener('input', function () {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 110) + 'px';
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && state.open && !panel.hidden) close();
    });
    // rudimentary focus trap
    panel.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var f = panel.querySelectorAll('button, [href], input, textarea');
      f = Array.prototype.filter.call(f, function (el) { return !el.hidden && el.offsetParent !== null; });
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });

    // any element on the page can open the chat: data-assist-open [data-assist-starter="…"]
    document.addEventListener('click', function (e) {
      var t = e.target && e.target.closest && e.target.closest('[data-assist-open]');
      if (!t) return;
      e.preventDefault();
      open(t.getAttribute('data-assist-starter') || '');
    });
  });
})();
