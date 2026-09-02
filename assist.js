/* leon --assist · the site's floating project assistant + event/utm plumbing.
   Same discipline as app.js: everything in guarded blocks, content never depends
   on this file. No frameworks, no keys — AI requests only ever go to our own
   backend (see server/), never to OpenAI directly. Optional consent-gated Google
   Ads conversion measurement is isolated below.

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

  /* ══ optional Google Ads conversion measurement ══════════
     Basic consent mode: the Google tag is not requested and no data is sent
     to Google until the visitor explicitly allows conversion measurement.
     Site code never intentionally passes contact fields to gtag, and ad
     personalization stays off. Automatic customer-data collection is a
     separate Google Ads account setting that must remain disabled there. */
  var ADS_ACCOUNT_ID = 'AW-18407115426';
  var ADS_CONSENT_KEY = 'leon_ads_consent_v1';
  var ADS_PENDING_KEY = 'leon_ads_pending_v1';
  var ADS_ACTIONS = {
    quote: 'AW-18407115426/ldkYCNKtreccEKKVmclE',
    booking: 'AW-18407115426/owGxCNWtreccEKKVmclE',
    phone: 'AW-18407115426/UrycCNitreccEKKVmclE',
    whatsapp: 'AW-18407115426/CGJTCNutreccEKKVmclE'
  };
  var adsConsent = '';
  var adsDefaultQueued = false;
  var adsTagStarted = false;
  var adsPending = [];
  var adsSent = {};
  var adsConsentReturnFocus = null;

  function adsGtag() {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    return window.gtag;
  }

  function queueAdsConsentDefault() {
    if (adsDefaultQueued) return;
    adsGtag()('consent', 'default', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: 'denied'
    });
    adsDefaultQueued = true;
  }

  function adsConsentUpdate(value) {
    adsGtag()('consent', 'update', {
      ad_storage: value,
      // This consent signal is required for tag-based conversion measurement.
      // It does not add contact data: user_data remains empty. Enhanced and
      // automatic customer-data collection must remain off in the Ads account.
      ad_user_data: value,
      ad_personalization: 'denied',
      analytics_storage: 'denied'
    });
  }

  function startGoogleAdsTag() {
    if (adsTagStarted || adsConsent !== 'granted') return;
    adsTagStarted = true;
    queueAdsConsentDefault();
    adsConsentUpdate('granted');
    adsGtag()('set', 'allow_ad_personalization_signals', false);
    adsGtag()('set', 'ads_data_redaction', true);
    // The site does not intentionally provide contact data to these events.
    // Account-level automatic customer-data collection is a separate Google
    // Ads setting and must remain disabled there.
    adsGtag()('set', 'user_data', {});
    adsGtag()('js', new Date());
    // Request suppression of the base page view. Google Ads may still emit a
    // standard consented configuration/page-view hit; the privacy disclosure
    // covers that platform behavior and the account's automatic extras are off.
    adsGtag()('config', ADS_ACCOUNT_ID, { send_page_view: false });
    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ADS_ACCOUNT_ID);
    script.setAttribute('data-leon-ads-tag', '');
    document.head.appendChild(script);
  }

  function adsKey(action, transactionId) {
    return action + ':' + (transactionId || 'session');
  }

  function adsAlreadySent(key) {
    if (adsSent[key]) return true;
    try { return sessionStorage.getItem('leon_ads_sent:' + key) === '1'; }
    catch (e) { return false; }
  }

  function markAdsSent(key) {
    adsSent[key] = true;
    try { sessionStorage.setItem('leon_ads_sent:' + key, '1'); } catch (e) {}
  }

  function adsTransactionId(action, value) {
    if (action === 'phone' || action === 'whatsapp') return '';
    if (typeof value !== 'string') return null;
    var id = value.trim();
    if (action === 'quote' && !/^lead_[A-Za-z0-9-]{16,59}$/.test(id)) return null;
    if (action === 'booking' && !/^[A-Za-z0-9._~-]{8,64}$/.test(id)) return null;
    return id;
  }

  function saveAdsPending() {
    try { sessionStorage.setItem(ADS_PENDING_KEY, JSON.stringify(adsPending)); } catch (e) {}
  }

  function loadAdsPending() {
    var saved = [];
    try { saved = JSON.parse(sessionStorage.getItem(ADS_PENDING_KEY) || '[]'); } catch (e) {}
    if (!Array.isArray(saved)) return;
    saved.forEach(function (item) {
      if (!item || !ADS_ACTIONS[item.action]) return;
      var id = adsTransactionId(item.action, item.transactionId);
      if (id === null) return;
      var key = adsKey(item.action, id);
      if (!adsAlreadySent(key) && !adsPending.some(function (pending) { return pending.key === key; })) {
        adsPending.push({ action: item.action, transactionId: id, key: key });
      }
    });
    saveAdsPending();
  }

  function sendAdsConversion(action, transactionId) {
    var sendTo = ADS_ACTIONS[action];
    if (!sendTo) return false;
    var id = adsTransactionId(action, transactionId);
    if (id === null) return false;
    var key = adsKey(action, id);
    if (adsAlreadySent(key) || adsConsent === 'denied') return false;
    if (adsConsent !== 'granted') {
      if (!adsPending.some(function (item) { return item.key === key; })) {
        adsPending.push({ action: action, transactionId: id, key: key });
        saveAdsPending();
      }
      return false;
    }
    startGoogleAdsTag();
    // Keep this empty. These actions measure counts, not contact data or lead
    // value. The separate automatic collection setting must remain disabled.
    var fields = { send_to: sendTo, user_data: {} };
    if (id) fields.transaction_id = id;
    adsGtag()('event', 'conversion', fields);
    markAdsSent(key);
    return true;
  }

  function flushAdsConversions() {
    var pending = adsPending.slice();
    adsPending = [];
    saveAdsPending();
    pending.forEach(function (item) {
      sendAdsConversion(item.action, item.transactionId);
    });
  }

  function consentCopy() {
    var lang = ((document.documentElement.getAttribute('lang') || 'en').slice(0, 2)).toLowerCase();
    var copy = {
      en: {
        title: 'Allow ad measurement?',
        body: 'Google Ads may use cookies to connect an ad click with a quote, booked call, phone click or WhatsApp click. Leon Builds does not intentionally send form entries or contact details; ad personalization stays off.',
        allow: 'Allow measurement', deny: 'No thanks', privacy: 'Privacy details'
      },
      es: {
        title: '\u00bfPermitir la medici\u00f3n de conversiones?',
        body: 'Google Ads puede usar cookies para relacionar un clic en un anuncio con una solicitud de presupuesto, una llamada reservada o un clic en tel\u00e9fono o WhatsApp. Leon Builds no env\u00eda intencionalmente datos del formulario ni datos de contacto. La personalizaci\u00f3n de anuncios sigue desactivada.',
        allow: 'Permitir medici\u00f3n', deny: 'No, gracias', privacy: 'Detalles de privacidad'
      },
      pt: {
        title: 'Permitir medi\u00e7\u00e3o de convers\u00f5es?',
        body: 'O Google Ads poder\u00e1 usar cookies para relacionar um clique no an\u00fancio a um pedido de or\u00e7amento, chamada agendada ou clique em telefone ou WhatsApp. A Leon Builds n\u00e3o envia intencionalmente dados do formul\u00e1rio nem dados de contato. A personaliza\u00e7\u00e3o de an\u00fancios continua desativada.',
        allow: 'Permitir medi\u00e7\u00e3o', deny: 'N\u00e3o, obrigado', privacy: 'Detalhes de privacidade'
      },
      zh: {
        title: '\u5141\u8bb8\u8f6c\u5316\u8861\u91cf\uff1f',
        body: 'Google Ads \u53ef\u80fd\u4f7f\u7528 Cookie\uff0c\u5c06\u5e7f\u544a\u70b9\u51fb\u4e0e\u62a5\u4ef7\u7533\u8bf7\u3001\u9884\u7ea6\u901a\u8bdd\u3001\u7535\u8bdd\u70b9\u51fb\u6216 WhatsApp \u70b9\u51fb\u5173\u8054\u3002Leon Builds \u4e0d\u4f1a\u6545\u610f\u53d1\u9001\u8868\u5355\u5185\u5bb9\u6216\u8054\u7cfb\u65b9\u5f0f\u3002\u5e7f\u544a\u4e2a\u6027\u5316\u4ecd\u4fdd\u6301\u5173\u95ed\u3002',
        allow: '\u5141\u8bb8\u8861\u91cf', deny: '\u4e0d\u7528\u4e86', privacy: '\u9690\u79c1\u8be6\u60c5'
      }
    };
    return copy[lang] || copy.en;
  }

  function ensureConsentBanner() {
    var banner = document.querySelector('[data-ads-consent]');
    if (banner) return banner;
    var copy = consentCopy();
    banner = document.createElement('section');
    banner.className = 'ads-consent';
    banner.hidden = true;
    banner.setAttribute('data-ads-consent', '');
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-modal', 'false');
    banner.setAttribute('aria-labelledby', 'ads-consent-title');
    banner.setAttribute('aria-describedby', 'ads-consent-description');
    banner.setAttribute('tabindex', '-1');
    banner.innerHTML = '<p class="ads-consent-title" id="ads-consent-title">' + copy.title + '</p>' +
      '<p id="ads-consent-description">' + copy.body + ' <a href="/privacy#conversion-measurement">' + copy.privacy + '</a>.</p>' +
      '<div><button type="button" data-ads-consent-allow>' + copy.allow + '</button>' +
      '<button type="button" data-ads-consent-deny>' + copy.deny + '</button></div>';
    document.body.appendChild(banner);
    return banner;
  }

  function showConsentBanner(focus) {
    var banner = ensureConsentBanner();
    banner.hidden = false;
    document.body.classList.add('ads-consent-open');
    if (focus) {
      var active = document.activeElement;
      if (active && active !== document.body && active !== banner) adsConsentReturnFocus = active;
      banner.focus();
    }
  }

  function hideConsentBanner() {
    var banner = document.querySelector('[data-ads-consent]');
    if (banner) banner.hidden = true;
    document.body.classList.remove('ads-consent-open');
    var returnFocus = adsConsentReturnFocus;
    adsConsentReturnFocus = null;
    if (returnFocus && typeof returnFocus.focus === 'function') {
      try { returnFocus.focus(); } catch (e) {}
    }
  }

  function setAdsConsent(value) {
    if (value !== 'granted' && value !== 'denied') return;
    adsConsent = value;
    try { localStorage.setItem(ADS_CONSENT_KEY, value); } catch (e) {}
    hideConsentBanner();
    if (value === 'granted') {
      startGoogleAdsTag();
      flushAdsConversions();
    } else {
      adsPending = [];
      saveAdsPending();
      if (adsTagStarted) {
        adsGtag()('set', 'ads_data_redaction', true);
        adsConsentUpdate('denied');
      }
    }
  }

  run(function () {
    queueAdsConsentDefault();
    loadAdsPending();
    try { adsConsent = localStorage.getItem(ADS_CONSENT_KEY) || ''; } catch (e) {}
    if (adsConsent === 'granted') startGoogleAdsTag();
    else if (adsConsent !== 'denied') { adsConsent = ''; showConsentBanner(true); }
    document.addEventListener('click', function (e) {
      if (e.target && e.target.closest && e.target.closest('[data-ads-consent-allow]')) setAdsConsent('granted');
      else if (e.target && e.target.closest && e.target.closest('[data-ads-consent-deny]')) setAdsConsent('denied');
      else if (e.target && e.target.closest && e.target.closest('[data-ads-consent-manage]')) {
        e.preventDefault();
        showConsentBanner(true);
      }
    });
  });

  /* ══ attribution + anonymous visit session ════════════════
     Keep first-touch immutable and last-touch separate. The earlier shape
     silently overwrote "first touch" every time a tagged link was opened,
     which made source reports impossible to interpret. No cookie or contact
     field is used: the session id lives only for the current browser tab. */
  var attribution = {};
  var analyticsSessionId = '';
  var ATTR_FIELDS = [
    ['utmSource', 'utm_source', 160, false],
    ['utmMedium', 'utm_medium', 160, false],
    ['utmCampaign', 'utm_campaign', 160, false],
    ['utmTerm', 'utm_term', 160, false],
    ['utmContent', 'utm_content', 160, false],
    ['gclid', 'gclid', 256, true],
    ['gbraid', 'gbraid', 256, true],
    ['wbraid', 'wbraid', 256, true],
    ['fbclid', 'fbclid', 256, true],
    ['msclkid', 'msclkid', 256, true]
  ];
  var ATTR_TTL_MS = 90 * 24 * 60 * 60 * 1000;

  function attrValue(value, max, tokenOnly) {
    var text = String(value || '').replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max);
    if (tokenOnly && !/^[A-Za-z0-9._~:+-]+$/.test(text)) return '';
    return text;
  }

  function referrerOrigin(value) {
    try {
      var url = new URL(String(value || ''));
      return /^(https?:)$/.test(url.protocol) ? url.origin : '';
    } catch (e) { return ''; }
  }

  function readAttributionQuery(qs) {
    var out = {};
    for (var i = 0; i < ATTR_FIELDS.length; i++) {
      var field = ATTR_FIELDS[i];
      var raw = qs.get(field[1]);
      if (field[0] === 'utmSource' && !raw) raw = qs.get('s');
      out[field[0]] = attrValue(raw, field[2], field[3]);
    }
    return out;
  }

  function applyAttribution(target) {
    var first = attribution.first || {};
    var last = attribution.last || {};
    for (var i = 0; i < ATTR_FIELDS.length; i++) {
      var name = ATTR_FIELDS[i][0];
      var title = name.charAt(0).toUpperCase() + name.slice(1);
      target[name] = attribution[name] || last[name] || first[name] || '';
      target['first' + title] = first[name] || '';
      target['last' + title] = last[name] || target[name] || '';
    }
    return target;
  }

  run(function () {
    var KEY = 'leon_attr';
    var SID = 'leon_analytics_session';
    try {
      analyticsSessionId = sessionStorage.getItem(SID) || '';
      if (!analyticsSessionId) {
        analyticsSessionId = (window.crypto && crypto.randomUUID)
          ? crypto.randomUUID()
          : String(Date.now()) + Math.random().toString(16).slice(2);
        sessionStorage.setItem(SID, analyticsSessionId);
      }
      var saved = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (saved && Number(saved.expiresAt) && Number(saved.expiresAt) < Date.now()) saved = null;
      var qs = new URLSearchParams(location.search);
      var campaign = readAttributionQuery(qs);
      var touch = {
        page: location.pathname,
        referrer: referrerOrigin(document.referrer),
        at: new Date().toISOString()
      };
      for (var ti = 0; ti < ATTR_FIELDS.length; ti++) {
        touch[ATTR_FIELDS[ti][0]] = campaign[ATTR_FIELDS[ti][0]] || '';
      }
      var taggedEntry = ATTR_FIELDS.some(function (field) { return !!campaign[field[0]]; });
      var externalEntry = false;
      try {
        externalEntry = !!touch.referrer && new URL(touch.referrer).hostname !== location.hostname;
      } catch (e) {}
      // Migrate the original flat record without throwing away its history.
      if (saved && !saved.first) {
        saved = {
          first: {
            page: saved.firstPage || '/', referrer: saved.referrer || '',
            utmSource: saved.utmSource || '', utmMedium: saved.utmMedium || '',
            utmCampaign: saved.utmCampaign || '', utmTerm: saved.utmTerm || '',
            utmContent: saved.utmContent || '', gclid: saved.gclid || '',
            gbraid: saved.gbraid || '', wbraid: saved.wbraid || '',
            fbclid: saved.fbclid || '', msclkid: saved.msclkid || '', at: saved.at || ''
          },
          last: {
            page: saved.firstPage || '/', referrer: saved.referrer || '',
            utmSource: saved.utmSource || '', utmMedium: saved.utmMedium || '',
            utmCampaign: saved.utmCampaign || '', utmTerm: saved.utmTerm || '',
            utmContent: saved.utmContent || '', gclid: saved.gclid || '',
            gbraid: saved.gbraid || '', wbraid: saved.wbraid || '',
            fbclid: saved.fbclid || '', msclkid: saved.msclkid || '', at: saved.at || ''
          }
        };
      }
      if (saved && saved.first) saved.first.referrer = referrerOrigin(saved.first.referrer);
      if (saved && saved.last) saved.last.referrer = referrerOrigin(saved.last.referrer);
      var refreshed = false;
      if (!saved) { saved = { first: touch, last: touch }; refreshed = true; }
      else if (taggedEntry || externalEntry) { saved.last = touch; refreshed = true; }
      if (!saved.first) saved.first = touch;
      if (!saved.last) saved.last = saved.first;

      // Legacy top-level fields keep existing lead forms backward-compatible.
      saved.firstPage = saved.first.page || '/';
      saved.referrer = saved.first.referrer || '';
      for (var si = 0; si < ATTR_FIELDS.length; si++) {
        var name = ATTR_FIELDS[si][0];
        saved[name] = saved.last[name] || saved.first[name] || '';
      }
      if (refreshed || !Number(saved.expiresAt)) saved.expiresAt = Date.now() + ATTR_TTL_MS;
      localStorage.setItem(KEY, JSON.stringify(saved));
      attribution = saved;
    } catch (e) {}
  });

  /* ══ event beacon (first-party, log-only) ════════════════ */
  function eventExtraValue(name, value) {
    if (typeof value !== 'string') return '';
    var text = value.trim();
    if (name === 'receipt') return /^lead_[A-Za-z0-9-]{16,59}$/.test(text) ? text : '';
    if (name === 'bookingUid') return /^[A-Za-z0-9._~-]{8,64}$/.test(text) ? text : '';
    if (name === 'status') return /^(accepted|failed)$/.test(text) ? text : '';
    if (name === 'service' || name === 'package') {
      return /^[a-z0-9][a-z0-9-]{0,63}$/.test(text) ? text : '';
    }
    return '';
  }

  function evt(name, extra) {
    extra = extra || {};
    try {
      var payload = {
        name: name, path: location.pathname,
        ref: String(attribution.referrer || '').slice(0, 200),
        utm: attribution.utmSource || '',
        medium: attribution.utmMedium || '',
        campaign: attribution.utmCampaign || '',
        firstPage: attribution.firstPage || '/',
        lastPage: location.pathname,
        firstRef: (attribution.first && attribution.first.referrer) || '',
        lastRef: (attribution.last && attribution.last.referrer) || '',
        firstUtm: (attribution.first && attribution.first.utmSource) || '',
        lastUtm: (attribution.last && attribution.last.utmSource) || '',
        firstMedium: (attribution.first && attribution.first.utmMedium) || '',
        lastMedium: (attribution.last && attribution.last.utmMedium) || '',
        firstCampaign: (attribution.first && attribution.first.utmCampaign) || '',
        lastCampaign: (attribution.last && attribution.last.utmCampaign) || '',
        sessionId: analyticsSessionId
      };
      applyAttribution(payload);
      // Correlation identifiers are safe; contact details never belong here.
      ['receipt', 'bookingUid', 'status', 'service', 'package'].forEach(function (k) {
        var value = eventExtraValue(k, extra[k]);
        if (value) payload[k] = value;
      });
      var body = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        navigator.sendBeacon(API_BASE + '/api/event', new Blob([body], { type: 'application/json' }));
      } else {
        fetch(API_BASE + '/api/event', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body, keepalive: true }).catch(function () {});
      }
    } catch (e) {}
    try {
      if (name === 'quote_lead_accepted' || name === 'lead_submit_success') {
        sendAdsConversion('quote', extra.receipt);
      }
      else if (name === 'calendar_booking_success') sendAdsConversion('booking', extra.bookingUid);
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
      var link = e.target && e.target.closest && e.target.closest('a[href]');
      if (!link) return;
      var href = String(link.getAttribute('href') || '');
      if (/^tel:/i.test(href)) sendAdsConversion('phone');
      else {
        try {
          var host = new URL(href, location.href).hostname.toLowerCase();
          if (host === 'wa.me' || host === 'api.whatsapp.com' || host === 'web.whatsapp.com') {
            sendAdsConversion('whatsapp');
          }
        } catch (err) {}
      }
    }, { passive: true });
  });

  /* A transcript is bounded by MESSAGE COUNT everywhere else, which says
     nothing about bytes: forty turns at 4k each is 160kb against a 48kb body
     limit, and `keepalive` is capped at 64KiB by the fetch spec. Budget by
     characters instead, keeping the most recent turns — those are the ones
     that say what the visitor actually wants. */
  /* A message is either a string or an array of parts once photos exist. This
     is the single place that flattens it, so the lead payload, sessionStorage
     and the transcript can never disagree about what was said. */
  function plainText(content) {
    if (typeof content === 'string') return content;
    if (!Array.isArray(content)) return '';
    var out = [];
    for (var i = 0; i < content.length; i++) {
      var p = content[i];
      if (!p) continue;
      if (p.type === 'input_text' && p.text) out.push(p.text);
      else if (p.type === 'input_image') out.push('[photo attached]');
    }
    return out.join(' ');
  }

  function budgetedHistory(history, maxChars) {
    var out = [], total = 0;
    for (var i = history.length - 1; i >= 0; i--) {
      var m = history[i];
      // Never a base64 photo: one would consume the whole budget and tell the
      // reader of the lead nothing a marker does not.
      var c = plainText(m.content);
      if (total + c.length > maxChars) {
        if (!out.length) out.unshift({ role: m.role, content: c.slice(-maxChars) });
        break;
      }
      out.unshift({ role: m.role, content: c });
      total += c.length;
    }
    return out;
  }

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
  // Keep attribution across a language switch and prefer this page's hreflang
  // counterpart. Falling back to a language home is still better than a 404.
  function langHref(v) {
    var hreflang = v === 'pt' ? 'pt-BR' : v;
    var alt = document.querySelector('link[rel="alternate"][hreflang="' + hreflang + '"]');
    var base = alt ? alt.getAttribute('href') : (LANG_PAGE[v] || '/');
    try {
      var u = new URL(base, location.origin);
      var current = new URLSearchParams(location.search);
      var allowed = [['s', 160, false]];
      ATTR_FIELDS.forEach(function (field) { allowed.push([field[1], field[2], field[3]]); });
      allowed.forEach(function (rule) {
        var value = attrValue(current.get(rule[0]), rule[1], rule[2]);
        if (value && !u.searchParams.has(rule[0])) u.searchParams.set(rule[0], value);
      });
      return u.origin === location.origin ? u.pathname + u.search + u.hash : u.href;
    } catch (e) { return LANG_PAGE[v] || '/'; }
  }

  /* ══ nonblocking first-visit language nudge ═══════════════
     Never put a choice gate in front of a quote or booking. Only show a small
     nudge when the browser itself prefers a supported non-English language;
     the permanent navigation switcher remains available to everyone else. */
  var langBar = null;
  run(function () {
    if (storedLang()) return;
    if (PAGE_LANG !== 'en') return;
    if (/^\/(call|quote)(\/|$)/.test(location.pathname)) return;
    try { if (localStorage.getItem('leon_lang_dismissed')) return; } catch (e) {}
    var guess = detectLang();
    if (!guess || guess === 'en') return;

    var bar = document.createElement('aside');
    bar.className = 'as-langbar';
    bar.setAttribute('aria-label', LANG_SWITCH[guess] || LANG_ASK);
    bar.innerHTML = '<button class="x" type="button" aria-label="close">\u2715</button>'
      + '<p>' + (LANG_SWITCH[guess] || LANG_ASK) + '</p><div class="opts"></div>';
    var opts = bar.querySelector('.opts');
    var choose = document.createElement('button');
    choose.type = 'button'; choose.className = 'go'; choose.lang = guess;
    choose.textContent = LANG_NAME[guess];
    var keep = document.createElement('button');
    keep.type = 'button'; keep.textContent = 'keep english';
    function close() {
      try { localStorage.setItem('leon_lang_dismissed', '1'); } catch (e) {}
      bar.remove(); langBar = null;
    }
    choose.addEventListener('click', function () {
      setLang(guess); evt('lang_pick_' + guess); close(); location.href = langHref(guess);
    });
    keep.addEventListener('click', function () { setLang('en'); evt('lang_pick_en'); close(); });
    bar.querySelector('.x').addEventListener('click', function () { evt('lang_prompt_dismiss'); close(); });
    opts.appendChild(choose); opts.appendChild(keep);
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

    // A second copy inside the burger menu. On a phone the nav has room for the
    // mark, the booking button and the burger — and that is all; the pills were
    // squeezing the wordmark down to nothing. CSS shows exactly one of the two.
    var menu = $('.nav-mid');
    if (menu) {
      var m = wrap.cloneNode(true);
      m.className = 'as-langpick in-menu';
      Array.prototype.forEach.call(m.querySelectorAll('a'), function (a) {
        a.addEventListener('click', function () {
          setLang(a.getAttribute('lang'));
          evt('lang_switch_' + a.getAttribute('lang'));
        });
      });
      menu.appendChild(m);
    }
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

  /* Every piece of injected UI follows the page/visitor language. The chat
     used to answer in four languages while its controls, consent note and
     lead form stayed English, which made the handoff feel untrustworthy. */
  var UI = {
    en: {
      launch: 'ask about your project', label: "leon's ai project assistant", assistantTitle: 'Project assistant',
      status: 'ai project assistant', leadOpen: 'send project', leadSent: 'sent ✓', fresh: 'new',
      freshTitle: 'start over', close: 'close chat',
      intro: "tell me what your business does and what part of the week is still done by hand — i'll suggest the smallest useful next step, a realistic starting range, and tell you when you do not need custom software.",
      leadIntro: '<b>Send this conversation securely to Leon.</b> He usually replies the same business day. You will get a receipt here; no email app is required.',
      name: 'name', email: 'email (required)', phone: 'phone (optional)', problem: 'what should Leon help with? (required)',
      submit: 'send securely', later: 'not yet', invalidEmail: 'that email does not look right.',
      sending: 'sending securely…', sent: 'Sent to Leon. Save this receipt:',
      offerTitle: 'Ready to involve Leon?', offerBody: 'Send this project and our conversation. No payment or commitment.',
      offerSend: 'Send this project to Leon', offerLater: 'Keep chatting',
      successTitle: 'Project sent to Leon', successBody: 'We received your request and saved this conversation for Leon. He usually replies to the email you provided the same business day.',
      receiptLabel: 'Submission receipt', successBack: 'Return to the conversation',
      book: 'Book a free 15-minute call', fallback: 'email Leon instead',
      failed: 'That did not reach the server. Your details are still here — retry, or use the email fallback.',
      attached: 'attached photo', remove: 'remove photo', attach: 'attach a photo',
      placeholder: 'describe your business, or attach a photo…', send: 'send',
      note: 'AI assistant — messages and photos may be processed to answer and scope your project. Never send passwords or payment details.',
      privacy: 'privacy', human: 'prefer a human?', emailHuman: 'email', callHuman: 'call',
      thinking: 'thinking', waking: 'waking the assistant — this may take about 30 seconds',
      upTo: 'you can attach up to ', notPhoto: 'that file is not a photo', unreadable: 'could not read that photo',
      photoOnly: 'here is a photo of what i have now.', streamFailed: 'The assistant stopped before finishing. Here is Leon directly:'
    },
    es: {
      launch: 'cuéntame tu proyecto', label: 'asistente de proyectos de Leon', assistantTitle: 'Asistente de proyecto',
      status: 'asistente de proyectos con IA', leadOpen: 'enviar proyecto', leadSent: 'enviado ✓', fresh: 'nuevo',
      freshTitle: 'empezar de nuevo', close: 'cerrar chat',
      intro: 'Cuéntame qué hace tu negocio y qué parte de la semana todavía haces a mano. Te sugeriré el paso útil más pequeño, un precio inicial realista y también te diré si no necesitas software a medida.',
      leadIntro: '<b>Envía esta conversación de forma segura a Leon.</b> Suele responder el mismo día laborable. Recibirás un comprobante aquí; no necesitas abrir el correo.',
      name: 'nombre', email: 'correo (obligatorio)', phone: 'teléfono (opcional)', problem: '¿en qué debe ayudarte Leon? (obligatorio)',
      submit: 'enviar de forma segura', later: 'ahora no', invalidEmail: 'ese correo no parece correcto.',
      sending: 'enviando de forma segura…', sent: 'Enviado a Leon. Guarda este comprobante:',
      offerTitle: '¿Listo para incluir a Leon?', offerBody: 'Envía este proyecto y nuestra conversación. Sin pago ni compromiso.',
      offerSend: 'Enviar este proyecto a Leon', offerLater: 'Seguir conversando',
      successTitle: 'Proyecto enviado a Leon', successBody: 'Tu solicitud y esta conversación se guardaron para Leon. Suele responder al correo que diste el mismo día laborable.',
      receiptLabel: 'Comprobante de envío', successBack: 'Volver a la conversación',
      book: 'Reservar una llamada gratuita de 15 minutos', fallback: 'enviar correo a Leon',
      failed: 'No llegó al servidor. Tus datos siguen aquí: inténtalo otra vez o usa el correo.',
      attached: 'foto adjunta', remove: 'quitar foto', attach: 'adjuntar una foto',
      placeholder: 'describe tu negocio o adjunta una foto…', send: 'enviar',
      note: 'El asistente con IA puede procesar mensajes y fotos para responder y definir el proyecto. No envíes contraseñas ni datos de pago.',
      privacy: 'privacidad', human: '¿prefieres una persona?', emailHuman: 'correo', callHuman: 'llamar',
      thinking: 'pensando', waking: 'iniciando el asistente — puede tardar unos 30 segundos',
      upTo: 'puedes adjuntar hasta ', notPhoto: 'ese archivo no es una foto', unreadable: 'no pude leer esa foto',
      photoOnly: 'aquí tienes una foto de lo que uso ahora.', streamFailed: 'El asistente se detuvo antes de terminar. Habla directamente con Leon:'
    },
    pt: {
      launch: 'conte sobre seu projeto', label: 'assistente de projetos do Leon', assistantTitle: 'Assistente de projeto',
      status: 'assistente de projetos com IA', leadOpen: 'enviar projeto', leadSent: 'enviado ✓', fresh: 'novo',
      freshTitle: 'começar de novo', close: 'fechar chat',
      intro: 'Conte o que seu negócio faz e qual parte da semana ainda é manual. Vou sugerir o menor próximo passo útil, uma faixa inicial realista e também dizer quando você não precisa de software sob medida.',
      leadIntro: '<b>Envie esta conversa com segurança ao Leon.</b> Ele costuma responder no mesmo dia útil. Você receberá um comprovante aqui; não precisa abrir o e-mail.',
      name: 'nome', email: 'e-mail (obrigatório)', phone: 'telefone (opcional)', problem: 'como o Leon pode ajudar? (obrigatório)',
      submit: 'enviar com segurança', later: 'agora não', invalidEmail: 'esse e-mail não parece correto.',
      sending: 'enviando com segurança…', sent: 'Enviado ao Leon. Guarde este comprovante:',
      offerTitle: 'Pronto para envolver o Leon?', offerBody: 'Envie este projeto e nossa conversa. Sem pagamento ou compromisso.',
      offerSend: 'Enviar este projeto ao Leon', offerLater: 'Continuar conversando',
      successTitle: 'Projeto enviado ao Leon', successBody: 'Seu pedido e esta conversa foram salvos para o Leon. Ele costuma responder no e-mail informado no mesmo dia útil.',
      receiptLabel: 'Comprovante de envio', successBack: 'Voltar para a conversa',
      book: 'Agendar uma conversa gratuita de 15 minutos', fallback: 'enviar e-mail ao Leon',
      failed: 'Não chegou ao servidor. Seus dados continuam aqui — tente novamente ou use o e-mail.',
      attached: 'foto anexada', remove: 'remover foto', attach: 'anexar uma foto',
      placeholder: 'descreva seu negócio ou anexe uma foto…', send: 'enviar',
      note: 'O assistente com IA pode processar mensagens e fotos para responder e definir o projeto. Não envie senhas nem dados de pagamento.',
      privacy: 'privacidade', human: 'prefere falar com uma pessoa?', emailHuman: 'e-mail', callHuman: 'ligar',
      thinking: 'pensando', waking: 'iniciando o assistente — pode levar cerca de 30 segundos',
      upTo: 'você pode anexar até ', notPhoto: 'esse arquivo não é uma foto', unreadable: 'não consegui ler essa foto',
      photoOnly: 'aqui está uma foto do que uso hoje.', streamFailed: 'O assistente parou antes de terminar. Fale direto com o Leon:'
    },
    zh: {
      launch: '聊聊你的项目', label: 'Leon 的项目助手', assistantTitle: '项目助手',
      status: 'AI 项目助手', leadOpen: '发送项目', leadSent: '已发送 ✓', fresh: '新对话',
      freshTitle: '重新开始', close: '关闭聊天',
      intro: '告诉我你的生意做什么，以及每周哪些工作还要手动完成。我会建议最小且有用的下一步、现实的起步范围；如果你不需要定制软件，我也会直接说明。',
      leadIntro: '<b>安全地把这段对话发送给 Leon。</b>他通常会在同一个工作日回复。页面会显示回执，无需打开邮件应用。',
      name: '姓名', email: '邮箱（必填）', phone: '电话（选填）', problem: '希望 Leon 帮你解决什么？（必填）',
      submit: '安全发送', later: '暂不发送', invalidEmail: '这个邮箱地址好像不正确。',
      sending: '正在安全发送…', sent: '已发送给 Leon。请保存回执：',
      offerTitle: '准备让 Leon 接手吗？', offerBody: '发送这个项目和我们的对话，无需付款，也没有承诺。',
      offerSend: '把这个项目发送给 Leon', offerLater: '继续聊天',
      successTitle: '项目已发送给 Leon', successBody: '你的请求和这段对话已为 Leon 保存。他通常会在同一个工作日回复你提供的邮箱。',
      receiptLabel: '提交回执', successBack: '返回对话',
      book: '预约免费的 15 分钟通话', fallback: '改用邮箱联系 Leon',
      failed: '没有成功到达服务器。你的资料仍保留在表格中，请重试或使用邮箱。',
      attached: '已附照片', remove: '移除照片', attach: '添加照片',
      placeholder: '描述你的生意，或添加一张照片…', send: '发送',
      note: 'AI 助手可能会处理消息和照片，以便回答并了解项目范围。请勿发送密码或付款资料。',
      privacy: '隐私', human: '想直接联系真人？', emailHuman: '邮件', callHuman: '电话',
      thinking: '正在思考', waking: '正在启动助手，可能需要约 30 秒',
      upTo: '最多可以添加 ', notPhoto: '这个文件不是照片', unreadable: '无法读取这张照片',
      photoOnly: '这是我现在使用方式的照片。', streamFailed: '助手未完成回复。你可以直接联系 Leon：'
    }
  };
  function lang() { return storedLang() || PAGE_LANG; }
  function ui() { return UI[lang()] || UI.en; }
  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>\"]/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[ch];
    });
  }
  var BOOKING_PAGE = { en: '/call', es: '/es/agendar', pt: '/pt/agendar', zh: '/zh/yuyue' };

  /* ══ the widget ══════════════════════════════════════════ */
  run(function () {
    if (window.__leonAssist) return;
    window.__leonAssist = true;

    var SS = 'leon_chat';
    var state = {
      open: false, busy: false, history: [], sessionId: '', warmed: false, firstSent: false,
      leadOfferShown: false, leadOfferDismissed: false, leadSubmitted: false,
      leadSuccessDismissed: false, leadReceipt: '', leadIdempotencyKey: ''
    };
    /* High-choice pages can keep attribution and explicit assistant triggers
       without adding a competing floating launcher. The mode is declarative so
       close() cannot accidentally make the launcher visible again. */
    var launcherEnabled = document.body.getAttribute('data-assistant-launcher') !== 'hidden';
    var t = ui();
    if (/^\/(call|quote|es\/agendar|pt\/agendar|zh\/yuyue)(\/|$)/.test(location.pathname)) {
      document.documentElement.classList.add('as-high-intent');
    }

    try {
      var saved = JSON.parse(sessionStorage.getItem(SS) || 'null');
      if (saved && Array.isArray(saved.history)) {
        state.history = saved.history;
        state.sessionId = saved.sessionId || '';
        state.leadOfferShown = saved.leadOfferShown === true;
        state.leadOfferDismissed = saved.leadOfferDismissed === true;
        state.leadSubmitted = saved.leadSubmitted === true;
        state.leadSuccessDismissed = saved.leadSuccessDismissed === true;
        state.leadReceipt = String(saved.leadReceipt || '').slice(0, 120);
        state.leadIdempotencyKey = String(saved.leadIdempotencyKey || '').slice(0, 96);
        state.firstSent = state.history.some(function (message) { return message && message.role === 'user'; });
      }
    } catch (e) {}
    if (!state.sessionId) {
      state.sessionId = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
    }
    function save() {
      // Photos are dropped to a marker before storing. sessionStorage caps around
      // 5MB and three downscaled photos would come close on their own — a quota
      // error here would throw away the whole transcript, not just the images.
      try {
        var slim = state.history.slice(-60).map(function (m) {
          return { role: m.role, content: plainText(m.content) };
        });
        sessionStorage.setItem(SS, JSON.stringify({
          history: slim, sessionId: state.sessionId,
          leadOfferShown: state.leadOfferShown,
          leadOfferDismissed: state.leadOfferDismissed,
          leadSubmitted: state.leadSubmitted,
          leadSuccessDismissed: state.leadSuccessDismissed,
          leadReceipt: state.leadReceipt,
          leadIdempotencyKey: state.leadIdempotencyKey
        }));
      } catch (e) {}
    }

    /* dom */
    var launch = document.createElement('button');
    launch.className = 'as-launch';
    launch.type = 'button';
    launch.setAttribute('aria-haspopup', 'dialog');
    launch.setAttribute('aria-label', t.launch);
    launch.innerHTML = '<i>[&gt;_]</i><span>' + esc(t.launch) + '</span>';

    var panel = document.createElement('section');
    panel.className = 'as-panel';
    panel.hidden = true;
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'true');
    panel.setAttribute('aria-label', t.label);
    panel.innerHTML =
      '<header class="as-head">' +
        '<span class="dot">[<span aria-hidden="true">•</span>]</span>' +
        '<div><h2 data-as-title>' + esc(t.assistantTitle) + '</h2><div class="st" data-as-status>' + esc(t.status) + '</div></div>' +
        '<span class="sp"></span>' +
        '<button class="as-hbtn as-hbtn-lead" type="button" data-as-lead-open>' + esc(t.leadOpen) + '</button>' +
        '<button class="as-hbtn" type="button" data-as-new title="' + esc(t.freshTitle) + '">' + esc(t.fresh) + '</button>' +
        '<button class="as-hbtn" type="button" data-as-close aria-label="' + esc(t.close) + '">✕</button>' +
      '</header>' +
      '<div class="as-log" data-as-log aria-live="polite"></div>' +
      '<section class="as-success" data-as-success hidden role="region" aria-labelledby="as-success-title" tabindex="-1">' +
        '<span class="as-success-mark" aria-hidden="true">✓</span>' +
        '<p class="as-success-kicker" role="status" aria-live="assertive" aria-atomic="true">' + esc(t.leadSent) + '</p>' +
        '<h3 id="as-success-title" data-as-success-title>' + esc(t.successTitle) + '</h3>' +
        '<p data-as-success-body>' + esc(t.successBody) + '</p>' +
        '<p class="as-success-receipt"><span data-as-receipt-label>' + esc(t.receiptLabel) + '</span><code data-as-receipt></code></p>' +
        '<div class="as-success-actions"><a data-as-success-book href="' + esc(BOOKING_PAGE[lang()] || BOOKING_PAGE.en) + '">' + esc(t.book) + '</a>' +
        '<button type="button" data-as-success-back>' + esc(t.successBack) + '</button></div>' +
      '</section>' +
      '<div class="as-lang" data-as-lang hidden><p></p><div class="opts"></div></div>' +
      '<div class="as-starts" data-as-starts></div>' +
      '<form class="as-lead" data-as-lead hidden>' +
        '<p>' + t.leadIntro + ' <a href="/privacy">' + esc(t.privacy) + '</a></p>' +
        '<label class="as-field"><span>' + esc(t.name) + '</span><input name="name" type="text" autocomplete="name"></label>' +
        '<div class="row2">' +
          '<label class="as-field"><span>' + esc(t.email) + '</span><input name="email" type="email" autocomplete="email" required></label>' +
          '<label class="as-field"><span>' + esc(t.phone) + '</span><input name="phone" type="tel" autocomplete="tel"></label>' +
        '</div>' +
        '<label class="as-field"><span>' + esc(t.problem) + '</span><textarea name="problem" rows="2" required></textarea></label>' +
        '<input name="website" type="text" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">' +
        '<p class="as-err" data-as-err role="alert" aria-live="assertive"></p>' +
        '<div class="acts"><button class="go" type="submit">' + esc(t.submit) + '</button><button class="no" type="button" data-as-lead-close>' + esc(t.later) + '</button></div>' +
      '</form>' +
      '<footer class="as-foot">' +
        '<div class="as-shots" data-as-shots hidden></div>' +
        '<div class="as-inrow">' +
          '<button class="as-clip" data-as-clip type="button" aria-label="' + esc(t.attach) + '" title="' + esc(t.attach) + '">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M21 11.5l-8.5 8.5a5 5 0 0 1-7-7l9-9a3.5 3.5 0 0 1 5 5l-9 9a2 2 0 0 1-3-3l8-8"/></svg>' +
          '</button>' +
          '<input type="file" data-as-file accept="image/png,image/jpeg,image/webp" multiple hidden>' +
          '<textarea class="as-in" data-as-in rows="1" placeholder="' + esc(t.placeholder) + '" aria-label="' + esc(t.placeholder) + '"></textarea>' +
          '<button class="as-send" data-as-send type="button" aria-label="' + esc(t.send) + '">↵</button>' +
        '</div>' +
        '<p class="as-note">' + esc(t.note) + ' <a href="/privacy">' + esc(t.privacy) + '</a><br>' + esc(t.human) +
          ' <a href="mailto:leondragon3798@gmail.com">' + esc(t.emailHuman) + '</a> · <a href="tel:+15108267735">' + esc(t.callHuman) + '</a></p>' +
      '</footer>';

    document.body.appendChild(launch);
    document.body.appendChild(panel);
    launch.hidden = !launcherEnabled;

    var log = $('[data-as-log]', panel);
    var startsBox = $('[data-as-starts]', panel);
    var input = $('[data-as-in]', panel);
    var sendBtn = $('[data-as-send]', panel);
    var fileIn = $('[data-as-file]', panel);
    var shotTray = $('[data-as-shots]', panel);
    var statusEl = $('[data-as-status]', panel);
    var leadForm = $('[data-as-lead]', panel);
    var leadErr = $('[data-as-err]', panel);
    var leadOpenBtn = $('[data-as-lead-open]', panel);
    var successView = $('[data-as-success]', panel);
    var lastFocus = null;

    function applyUi() {
      var launchText = $('span', launch); if (launchText) launchText.textContent = t.launch;
      launch.setAttribute('aria-label', t.launch);
      panel.setAttribute('aria-label', t.label);
      $('[data-as-title]', panel).textContent = t.assistantTitle;
      if (!state.busy) statusEl.textContent = t.status;
      leadOpenBtn.textContent = state.leadSubmitted ? t.leadSent : t.leadOpen;
      leadOpenBtn.classList.toggle('is-sent', state.leadSubmitted);
      leadOpenBtn.setAttribute('aria-label', state.leadSubmitted ? t.successTitle : t.offerSend);
      var fresh = $('[data-as-new]', panel); fresh.textContent = t.fresh; fresh.title = t.freshTitle;
      $('[data-as-close]', panel).setAttribute('aria-label', t.close);
      var leadIntro = leadForm.firstElementChild;
      if (leadIntro) leadIntro.innerHTML = t.leadIntro + ' <a href="/privacy">' + esc(t.privacy) + '</a>';
      var fieldNames = [t.name, t.email, t.phone, t.problem];
      Array.prototype.forEach.call(leadForm.querySelectorAll('.as-field > span'), function (span, i) {
        if (fieldNames[i]) span.textContent = fieldNames[i];
      });
      $('[data-as-lead] button[type="submit"]', panel).textContent = t.submit;
      $('[data-as-lead-close]', panel).textContent = t.later;
      $('[data-as-success-title]', panel).textContent = t.successTitle;
      $('[data-as-success-body]', panel).textContent = t.successBody;
      $('[data-as-receipt-label]', panel).textContent = t.receiptLabel;
      $('[data-as-success-book]', panel).textContent = t.book;
      $('[data-as-success-book]', panel).href = BOOKING_PAGE[lang()] || BOOKING_PAGE.en;
      $('[data-as-success-back]', panel).textContent = t.successBack;
      $('.as-success-kicker', panel).textContent = t.leadSent;
      var clip = $('[data-as-clip]', panel); clip.title = t.attach; clip.setAttribute('aria-label', t.attach);
      input.placeholder = t.placeholder; input.setAttribute('aria-label', t.placeholder);
      sendBtn.setAttribute('aria-label', t.send);
      var note = $('.as-note', panel);
      note.innerHTML = esc(t.note) + ' <a href="/privacy">' + esc(t.privacy) + '</a><br>' + esc(t.human)
        + ' <a href="mailto:leondragon3798@gmail.com">' + esc(t.emailHuman) + '</a> · '
        + '<a href="tel:+15108267735">' + esc(t.callHuman) + '</a>';
    }

    function msgEl(role, text, pics) {
      var d = document.createElement('div');
      d.className = 'as-msg ' + (role === 'user' ? 'u' : role === 'sys' ? 'sys' : 'a');
      d.textContent = text || '';
      if (pics && pics.length) {
        var row = document.createElement('div');
        row.className = 'as-msgpics';
        pics.forEach(function (sh) {
          var im = document.createElement('img');
          im.src = sh.dataUrl || sh;
          im.alt = t.attached;
          row.appendChild(im);
        });
        d.appendChild(row);
      }
      log.appendChild(d);
      log.scrollTop = log.scrollHeight;
      return d;
    }
    function renderHistory() {
      if (state.leadSubmitted && !state.leadSuccessDismissed) {
        showLeadSuccess(state.leadReceipt, false);
        return;
      }
      hideLeadSuccess();
      log.innerHTML = '';
      if (!state.history.length) {
        msgEl('assistant', t.intro);
      }
      state.history.forEach(function (m) { msgEl(m.role, plainText(m.content)); });
      renderConversionOffer();
      renderStarters();
      renderLangChoice();
    }

    function userConversationText() {
      return state.history
        .filter(function (m) { return m.role === 'user'; })
        .map(function (m) { return plainText(m.content).trim(); })
        .filter(Boolean);
    }

    function directSendIntent(text) {
      return /\b(send|submit|forward)\b.{0,35}\b(leon|project|conversation|this)\b|\b(leon|project|conversation|this)\b.{0,35}\b(send|submit|forward)\b/i.test(text)
        || /(envia|enviar|manda|mandar).{0,25}(leon|projeto|conversa)|(leon|projeto|conversa).{0,25}(envia|enviar|manda|mandar)/i.test(text)
        || /(envía|enviar|manda|mandar).{0,25}(leon|proyecto|conversación)|(leon|proyecto|conversación).{0,25}(envía|enviar|manda|mandar)/i.test(text)
        || /(发给|发送|提交).{0,12}(Leon|项目|对话)|(Leon|项目|对话).{0,12}(发给|发送|提交)/i.test(text);
    }

    function affirmativeIntent(text) {
      return /^(yes|yeah|yep|sure|ok|okay|please|do it|send it|go ahead)[.!\s]*$/i.test(text)
        || /^(sim|claro|pode|manda|envia|por favor)[.!\s]*$/i.test(text)
        || /^(sí|si|claro|vale|envíalo|mandalo|por favor)[.!\s]*$/i.test(text)
        || /^(好|好的|可以|发吧|发送|请发)[。！!\s]*$/.test(text);
    }

    function readyForHandoff() {
      var userText = userConversationText();
      var chars = userText.join(' ').length;
      var latest = userText[userText.length - 1] || '';
      return directSendIntent(latest) || chars >= 80 || (userText.length >= 2 && chars >= 24);
    }

    function markHandoffReady() {
      if (state.leadSubmitted || state.leadOfferShown || !readyForHandoff()) return false;
      state.leadOfferShown = true;
      state.leadOfferDismissed = false;
      save();
      evt('chat_handoff_offer_shown');
      return true;
    }

    function renderConversionOffer() {
      var old = $('[data-as-convert]', log);
      if (old) old.remove();
      if (!state.leadOfferShown || state.leadOfferDismissed || state.leadSubmitted) return;
      var box = document.createElement('section');
      box.className = 'as-convert';
      box.setAttribute('data-as-convert', '');
      box.setAttribute('aria-label', t.offerTitle);
      box.innerHTML = '<p class="as-convert-kicker">' + esc(t.offerTitle) + '</p>'
        + '<p>' + esc(t.offerBody) + '</p>'
        + '<div><button class="as-convert-go" type="button" data-as-convert-go>' + esc(t.offerSend) + '</button>'
        + '<button class="as-convert-later" type="button" data-as-convert-later>' + esc(t.offerLater) + '</button></div>';
      log.appendChild(box);
      log.scrollTop = log.scrollHeight;
    }

    function hideLeadSuccess() {
      panel.classList.remove('as-is-sent');
      successView.hidden = true;
    }

    function showLeadSuccess(receipt, shouldFocus) {
      state.leadSubmitted = true;
      state.leadSuccessDismissed = false;
      state.leadReceipt = String(receipt || state.leadReceipt || '').slice(0, 120);
      state.leadOfferShown = true;
      save();
      applyUi();
      $('[data-as-receipt]', successView).textContent = state.leadReceipt;
      successView.hidden = false;
      leadForm.hidden = true;
      panel.classList.add('as-is-sent');
      if (shouldFocus) {
        try { successView.focus({ preventScroll: true }); } catch (e) { successView.focus(); }
        try { successView.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'nearest' }); } catch (e) {}
      }
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
          t = ui();
          evt('lang_pick_' + v);
          box.hidden = true;
          applyUi();
          renderHistory();
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
      setTimeout(function () {
        if (state.leadSubmitted && !state.leadSuccessDismissed) successView.focus();
        else input.focus();
      }, 60);
      if (starter) send(starter);
    }
    function close() {
      panel.hidden = true; launch.hidden = !launcherEnabled;
      state.open = false;
      document.documentElement.style.overflow = '';
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function setBusy(b) {
      state.busy = b;
      sendBtn.disabled = b;
      statusEl.textContent = b ? t.thinking + '…' : t.status;
    }


    /* ══ photo attachments ═══════════════════════════════════════
       The assistant kept offering to look at a photo of a menu or a
       spreadsheet while the widget had no way to send one — it was inventing a
       capability, and the visitor who took it up hit nothing. Now it is real.

       Downscaled in the browser before it ever leaves the phone: a modern
       camera JPEG is 3-8MB, which is slow on the restaurant wifi this is used
       on and pointless for a model that reads it at ~1024px anyway. 1280px on
       the long edge at quality .72 lands around 150-350kb. */
    var statusTimer = null;
    function status(msg) {
      if (!statusEl) return;
      statusEl.textContent = msg;
      clearTimeout(statusTimer);
      statusTimer = setTimeout(function () {
        if (!state.busy) statusEl.textContent = t.status;
      }, 3200);
    }

    var MAX_SHOTS = 3;
    var shots = [];   // [{ id, name, dataUrl }]

    function downscale(file) {
      return new Promise(function (resolve, reject) {
        var url = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function () {
          try {
            var max = 1280;
            var w = img.naturalWidth, h = img.naturalHeight;
            var scale = Math.min(1, max / Math.max(w, h));
            var cw = Math.max(1, Math.round(w * scale));
            var ch = Math.max(1, Math.round(h * scale));
            var c = document.createElement('canvas');
            c.width = cw; c.height = ch;
            c.getContext('2d').drawImage(img, 0, 0, cw, ch);
            var out = c.toDataURL('image/jpeg', 0.72);
            URL.revokeObjectURL(url);
            resolve(out);
          } catch (e) { URL.revokeObjectURL(url); reject(e); }
        };
        img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('not an image')); };
        img.src = url;
      });
    }

    function renderShots() {
      shotTray.innerHTML = '';
      shotTray.hidden = !shots.length;
      shots.forEach(function (sh) {
        var chip = document.createElement('div');
        chip.className = 'as-shot';
        var im = document.createElement('img');
        im.src = sh.dataUrl; im.alt = sh.name || t.attached;
        var x = document.createElement('button');
        x.type = 'button'; x.setAttribute('aria-label', t.remove); x.textContent = '\u2715';
        x.addEventListener('click', function () {
          shots = shots.filter(function (o) { return o.id !== sh.id; });
          renderShots();
        });
        chip.appendChild(im); chip.appendChild(x);
        shotTray.appendChild(chip);
      });
    }

    function addFiles(list) {
      var files = Array.prototype.slice.call(list || []);
      if (!files.length) return;
      var room = MAX_SHOTS - shots.length;
      if (room <= 0) { status(t.upTo + MAX_SHOTS); return; }
      files.slice(0, room).forEach(function (f) {
        if (!/^image\/(png|jpeg|webp)$/.test(f.type)) { status(t.notPhoto); return; }
        downscale(f).then(function (dataUrl) {
          shots.push({ id: String(Date.now()) + Math.random(), name: f.name, dataUrl: dataUrl });
          renderShots();
          evt('chat_photo_attached');
        }).catch(function () { status(t.unreadable); });
      });
      fileIn.value = '';
    }

    fileIn.addEventListener('change', function () { addFiles(fileIn.files); });

    // paste a screenshot straight into the box
    input.addEventListener('paste', function (e) {
      var items = (e.clipboardData && e.clipboardData.items) || [];
      var imgs = [];
      for (var i = 0; i < items.length; i++) {
        if (items[i].kind === 'file' && /^image\//.test(items[i].type)) {
          var f = items[i].getAsFile(); if (f) imgs.push(f);
        }
      }
      if (imgs.length) { e.preventDefault(); addFiles(imgs); }
    });

    function send(text) {
      text = (text || input.value || '').trim();
      // A photo on its own is a complete message — "here is my menu" needs no
      // sentence — so an empty box with an attachment must still send.
      if ((!text && !shots.length) || state.busy) return;
      var acceptedVisibleOffer = state.leadOfferShown && !state.leadOfferDismissed && affirmativeIntent(text);
      var requestedDirectSend = directSendIntent(text);
      input.value = ''; input.style.height = '';
      startsBox.innerHTML = '';
      var lbox = $('[data-as-lang]', panel); if (lbox) lbox.hidden = true;
      if (!state.firstSent) { state.firstSent = true; evt('chat_first_message'); }

      var sending = shots.slice();
      shots = []; renderShots();

      if (sending.length) {
        var parts = [{ type: 'input_text', text: text || t.photoOnly }];
        sending.forEach(function (sh) {
          parts.push({ type: 'input_image', image_url: sh.dataUrl });
        });
        state.history.push({ role: 'user', content: parts });
        msgEl('user', text, sending);
      } else {
        state.history.push({ role: 'user', content: text });
        msgEl('user', text);
      }
      if (acceptedVisibleOffer || requestedDirectSend) {
        if (!state.leadOfferShown) {
          state.leadOfferShown = true;
          evt('chat_handoff_offer_shown');
        }
        save();
        evt('chat_handoff_offer_click');
        openLead();
        return;
      }
      save();
      setBusy(true);

      var think = document.createElement('div');
      think.className = 'as-think';
      think.innerHTML = esc(t.thinking) + ' <i>▌</i>';
      log.appendChild(think); log.scrollTop = log.scrollHeight;

      var slowNote = setTimeout(function () {
        think.innerHTML = esc(t.waking) + ' <i>▌</i>';
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
          handoffOffered: state.leadOfferShown || state.leadSubmitted,
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
          if (!String(full || '').trim()) throw new Error('empty assistant response');
          state.history.push({ role: 'assistant', content: full });
          var newlyReady = markHandoffReady();
          save();
          if (newlyReady) renderConversionOffer();
        });
      }).catch(function (err) {
        clearTimeout(slowNote);
        think.remove();
        var m = (err && err.name === 'AbortError') ? TIMEOUT_MSG[lang()] || TIMEOUT_MSG.en : t.streamFailed;
        msgEl('sys', m);
        // A failed reply must not end the conversation. Give them the channels
        // that always work, as buttons — not an address to copy by hand.
        handoffRow();
        if (!state.leadSubmitted && !state.leadOfferShown) {
          state.leadOfferShown = true;
          state.leadOfferDismissed = false;
          save();
          evt('chat_handoff_offer_shown');
          renderConversionOffer();
        }
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
      // WeChat has no reliable add-friend URL. Keep it first for Chinese and
      // copy the visible ID; phone and email remain honest fallbacks.
      zh: [['复制微信号 leon34695820', '#wechat', 'leon34695820', '已复制微信号，去微信粘贴添加'], ['打电话 (510) 826-7735', 'tel:+15108267735'], ['发邮件', 'mailto:leondragon3798@gmail.com?subject=项目']],
      es: [['whatsapp', 'https://wa.me/15108267735'], ['llamar (510) 826-7735', 'tel:+15108267735'], ['email', 'mailto:leondragon3798@gmail.com']]
    };
    function copyContact(value, done) {
      var fallback = function () {
        var t = document.createElement('textarea');
        t.value = value;
        t.setAttribute('readonly', '');
        t.style.position = 'fixed';
        t.style.left = '-9999px';
        document.body.appendChild(t);
        t.select();
        try { document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(t);
        done();
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).then(done, fallback);
      } else {
        fallback();
      }
    }
    function handoffRow() {
      var opts = HANDOFF[lang()] || HANDOFF.en;
      var box = document.createElement('div');
      box.className = 'as-starts';
      opts.forEach(function (o) {
        var a = document.createElement('a');
        a.href = o[1];
        a.textContent = o[0];
        if (o[1].indexOf('http') === 0) { a.target = '_blank'; a.rel = 'noopener'; }
        a.addEventListener('click', function (e) {
          evt('handoff_' + lang());
          if (!o[2]) return;
          e.preventDefault();
          var original = a.textContent;
          copyContact(o[2], function () {
            a.textContent = o[3] || 'copied';
            evt('handoff_' + lang() + '_copy');
            setTimeout(function () { a.textContent = original; }, 2200);
          });
        });
        box.appendChild(a);
      });
      log.appendChild(box);
      log.scrollTop = log.scrollHeight;
    }

    /* lead form */
    function openLead() {
      if (state.leadSubmitted) {
        showLeadSuccess(state.leadReceipt, true);
        return;
      }
      hideLeadSuccess();
      leadForm.hidden = false;
      leadErr.textContent = '';
      var problem = $('textarea[name="problem"]', leadForm);
      if (problem && !problem.value) {
        var recentUser = state.history
          .filter(function (m) { return m.role === 'user'; })
          .slice(-4)
          .map(function (m) { return plainText(m.content).trim(); })
          .filter(Boolean);
        if (recentUser.length) problem.value = recentUser.join('\n').slice(0, 1500);
      }
      evt('lead_form_open');
      $('input[name="email"]', leadForm).focus();
    }

    function mailFallback(name, email, phone) {
      var talk = state.history.slice(-20).map(function (m) {
        return (m.role === 'user' ? 'visitor: ' : 'assistant: ') + plainText(m.content).trim();
      }).join('\n\n');
      var body = 'name: ' + (name || '(not given)') + '\nemail: ' + email + (phone ? '\nphone: ' + phone : '')
        + '\n\nsite conversation:\n\n' + talk
        + '\n\n— leonbuilds.org' + (location.pathname !== '/' ? ' (' + location.pathname + ')' : '');
      if (body.length > 1800) body = body.slice(0, 1800) + '\n…';
      return 'mailto:leondragon3798@gmail.com?subject=' + encodeURIComponent('project inquiry' + (name ? ' — ' + name : ''))
        + '&body=' + encodeURIComponent(body);
    }

    function leadActions(mailHref) {
      var box = document.createElement('div');
      box.className = 'as-starts as-result-actions';
      var book = document.createElement('a');
      book.href = BOOKING_PAGE[lang()] || BOOKING_PAGE.en;
      book.textContent = t.book;
      book.addEventListener('click', function () { evt('lead_booking_click'); });
      var email = document.createElement('a');
      email.href = mailHref;
      email.textContent = t.fallback;
      email.addEventListener('click', function () { evt('lead_email_fallback'); });
      box.appendChild(book); box.appendChild(email);
      log.appendChild(box);
      log.scrollTop = log.scrollHeight;
    }

    function postLead(payload, isRetry) {
      return fetch(API_BASE + '/api/lead', {
        method: 'POST', keepalive: true,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(function (res) {
        return res.json().catch(function () { return {}; }).then(function (data) {
          if (res.ok && data.ok) return data;
          if (!isRetry && res.status >= 500) {
            evt('lead_submit_retry');
            return postLead(payload, true);
          }
          throw new Error(data.error || 'lead submission failed');
        });
      }, function (error) {
        if (!isRetry) {
          evt('lead_submit_retry');
          return postLead(payload, true);
        }
        throw error;
      });
    }

    leadForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = new FormData(leadForm);
      var email = String(f.get('email') || '').trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { leadErr.textContent = t.invalidEmail; return; }
      leadErr.textContent = '';
      var name = String(f.get('name') || ''), phone = String(f.get('phone') || '');
      var problem = String(f.get('problem') || '').trim();
      if (!problem) { leadErr.textContent = t.problem; return; }
      var summary = budgetedHistory(state.history, 7000).map(function (m) {
        return (m.role === 'user' ? 'visitor: ' : 'assistant: ') + plainText(m.content);
      }).join('\n\n');
      if (!state.leadIdempotencyKey) {
        state.leadIdempotencyKey = 'leadreq_' + ((window.crypto && crypto.randomUUID)
          ? crypto.randomUUID()
          : String(Date.now()) + '-' + Math.random().toString(16).slice(2));
        save();
      }
      var leadBody = {
        via: 'chat', name: name, email: email, phone: phone,
        website: String(f.get('website') || ''), problem: problem,
        idempotencyKey: state.leadIdempotencyKey,
        conversationSummary: summary,
        sourcePage: location.pathname,
        referrer: attribution.referrer || '',
        firstPage: (attribution.first && attribution.first.page) || attribution.firstPage || '/',
        firstReferrer: (attribution.first && attribution.first.referrer) || '',
        lastPage: location.pathname,
        lastReferrer: (attribution.last && attribution.last.referrer) || '',
        analyticsSessionId: analyticsSessionId,
        chatSessionId: state.sessionId
      };
      applyAttribution(leadBody);
      var submit = $('button[type="submit"]', leadForm);
      var original = submit.textContent;
      submit.disabled = true;
      submit.textContent = t.sending;
      evt('lead_submit_attempt');
      postLead(leadBody, false).then(function (data) {
        var receipt = String(data.receipt || data.receiptId || '');
        if (!/^lead_[A-Za-z0-9-]{16,}$/.test(receipt)) throw new Error('missing receipt');
        evt('lead_submit_success', { receipt: receipt, status: 'accepted' });
        showLeadSuccess(receipt, true);
      }).catch(function () {
        evt('lead_submit_failed', { status: 'failed' });
        leadErr.textContent = t.failed;
        var old = $('.as-inline-fallback', leadForm);
        if (!old) {
          var fallback = document.createElement('a');
          fallback.className = 'as-inline-fallback';
          fallback.href = mailFallback(name, email, phone);
          fallback.textContent = t.fallback;
          fallback.addEventListener('click', function () { evt('lead_email_fallback'); });
          leadErr.insertAdjacentElement('afterend', fallback);
        }
      }).finally(function () {
        submit.disabled = false;
        submit.textContent = original;
      });
    });

    /* wiring */
    launch.addEventListener('click', function () { open(); });
    launch.addEventListener('mouseenter', warm, { once: false });
    launch.addEventListener('pointerdown', warm, { once: true });
    panel.addEventListener('click', function (e) {
      if (e.target.closest('[data-as-close]')) close();
      if (e.target.closest('[data-as-lead-open]')) {
        evt(state.leadSubmitted ? 'lead_success_reopened' : 'chat_handoff_offer_click');
        openLead();
      }
      if (e.target.closest('[data-as-convert-go]')) {
        evt('chat_handoff_offer_click');
        openLead();
      }
      if (e.target.closest('[data-as-convert-later]')) {
        state.leadOfferDismissed = true;
        save();
        evt('chat_handoff_offer_dismissed');
        renderConversionOffer();
        input.focus();
      }
      if (e.target.closest('[data-as-lead-close]')) leadForm.hidden = true;
      if (e.target.closest('[data-as-success-book]')) evt('lead_booking_click');
      if (e.target.closest('[data-as-success-back]')) {
        state.leadSuccessDismissed = true;
        save();
        hideLeadSuccess();
        renderHistory();
        input.focus();
      }
      if (e.target.closest('[data-as-new]')) {
        state.history = [];
        state.sessionId = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
        state.leadOfferShown = false;
        state.leadOfferDismissed = false;
        state.leadSubmitted = false;
        state.leadSuccessDismissed = false;
        state.leadReceipt = '';
        state.leadIdempotencyKey = '';
        state.firstSent = false;
        leadForm.reset();
        leadForm.hidden = true;
        hideLeadSuccess();
        applyUi();
        save();
        renderHistory();
        input.focus();
      }
      if (e.target.closest('[data-as-clip]')) { fileIn.click(); return; }
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
