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
      if (!saved) {
        saved = {
          firstPage: location.pathname,
          referrer: (document.referrer || '').slice(0, 200),
          utmSource: qs.get('utm_source') || '',
          utmMedium: qs.get('utm_medium') || '',
          utmCampaign: qs.get('utm_campaign') || ''
        };
        localStorage.setItem(KEY, JSON.stringify(saved));
      } else if (qs.get('utm_source')) {
        saved.utmSource = qs.get('utm_source');
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
        ref: attribution.referrer || '', utm: attribution.utmSource || ''
      });
      if (navigator.sendBeacon) {
        navigator.sendBeacon(API_BASE + '/api/event', new Blob([body], { type: 'application/json' }));
      } else {
        fetch(API_BASE + '/api/event', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body, keepalive: true }).catch(function () {});
      }
    } catch (e) {}
  }
  window.leonEvt = evt;

  // declarative events: any element with data-evt fires on click
  run(function () {
    document.addEventListener('click', function (e) {
      var el = e.target && e.target.closest && e.target.closest('[data-evt]');
      if (el) evt(el.getAttribute('data-evt'));
    }, { passive: true });
  });

  /* ══ contextual starter prompts ══════════════════════════ */
  function starters() {
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
      '<div class="as-starts" data-as-starts></div>' +
      '<form class="as-lead" data-as-lead hidden>' +
        '<p><b>send this conversation to leon.</b> he reads every one and replies himself — usually same day.</p>' +
        '<input name="name" type="text" placeholder="name" autocomplete="name">' +
        '<div class="row2">' +
          '<input name="email" type="email" placeholder="email (required)" autocomplete="email" required>' +
          '<input name="phone" type="tel" placeholder="phone (optional)" autocomplete="tel">' +
        '</div>' +
        '<input name="website" type="text" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">' +
        '<p class="as-err" data-as-err></p>' +
        '<div class="acts"><button class="go" type="submit">send it</button><button class="no" type="button" data-as-lead-close>not yet</button></div>' +
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
        var m = (err && err.name === 'AbortError') ? 'that took too long — try once more.' : (err.message || 'connection failed.');
        msgEl('sys', m + " you can always email leon directly: leondragon3798@gmail.com");
      }).finally(function () {
        clearTimeout(timeout);
        setBusy(false);
        input.focus();
      });
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
      leadErr.textContent = 'sending…';
      fetch(API_BASE + '/api/lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          via: 'chat',
          name: String(f.get('name') || ''),
          email: email,
          phone: String(f.get('phone') || ''),
          website: String(f.get('website') || ''),
          messages: state.history.slice(-40),
          problem: (state.history.filter(function (m) { return m.role === 'user'; })[0] || {}).content || '',
          sourcePage: location.pathname,
          referrer: attribution.referrer || '',
          utmSource: attribution.utmSource || '',
          utmMedium: attribution.utmMedium || '',
          utmCampaign: attribution.utmCampaign || ''
        })
      }).then(function (res) { return res.json().then(function (j) { return { ok: res.ok, j: j }; }); })
        .then(function (r) {
          if (!r.ok) { leadErr.textContent = r.j.error || 'could not send — email leon instead.'; return; }
          leadForm.hidden = true;
          evt('lead_submit');
          msgEl('sys', 'sent. leon will get back to you at ' + email + '.');
        })
        .catch(function () { leadErr.textContent = 'network problem — email leondragon3798@gmail.com instead.'; });
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
