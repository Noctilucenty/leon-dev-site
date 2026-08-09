/* leon — site behaviour.
   Every feature lives in its own run() block on purpose: a throw in one must not
   take the rest of the page down. Content is visible by default; JS only adds. */

(function () {
  'use strict';

  var run = function (fn) { try { fn(); } catch (e) { /* fail soft */ } };
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = window.matchMedia && window.matchMedia('(pointer: fine)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var lerp = function (a, b, t) { return a + (b - a) * t; };

  /* ══ 1. dithered pixel canvases ═════════════════════════════
     Renders a low-res field, thresholds it through an 8x8 Bayer
     matrix and lets CSS scale it up with image-rendering:pixelated.
     That ordered threshold is what makes it read as a dither
     rather than as noise. */
  run(function () {
    if (reduced) return;
    var canvases = $$('canvas[data-dither]');
    if (!canvases.length) return;

    // 8x8 Bayer, normalised 0..1
    var B = [
      0, 32, 8, 40, 2, 34, 10, 42,
      48, 16, 56, 24, 50, 18, 58, 26,
      12, 44, 4, 36, 14, 46, 6, 38,
      60, 28, 52, 20, 62, 30, 54, 22,
      3, 35, 11, 43, 1, 33, 9, 41,
      51, 19, 59, 27, 49, 17, 57, 25,
      15, 47, 7, 39, 13, 45, 5, 37,
      63, 31, 55, 23, 61, 29, 53, 21
    ].map(function (v) { return (v + 0.5) / 64; });

    var PX = 6;               // device px per dither cell
    var RGB = [155, 140, 255]; // the purple

    /* Gain is deliberately below 1: the field has to sit *under* most Bayer
       thresholds or the whole canvas lights up and eats the nav. */
    var fields = {
      // slow diagonal swell, densest toward the right of the headline
      hero: function (x, y, t) {
        var v = Math.sin(x * 2.1 + t * 0.7) * 0.5 + Math.sin(y * 3.3 - t * 0.5) * 0.35
              + Math.sin((x + y) * 1.6 + t * 0.9) * 0.3;
        var fall = Math.max(0, 1 - Math.abs(x - 0.86) * 1.5) * Math.max(0, 1 - y * 1.1);
        return (v * 0.5 + 0.5) * fall * 0.78;
      },
      // a rising bloom from the bottom centre
      cta: function (x, y, t) {
        var dx = x - 0.5, dy = y - 1.05;
        var d = Math.sqrt(dx * dx * 0.7 + dy * dy);
        var v = Math.sin(d * 9 - t * 1.4) * 0.5 + 0.5;
        return v * Math.max(0, 1 - d * 1.35) * 0.8;
      }
    };

    canvases.forEach(function (cv) {
      var field = fields[cv.getAttribute('data-dither')] || fields.hero;
      var ctx = cv.getContext('2d', { alpha: true });
      if (!ctx) return;
      var w = 0, h = 0, img = null, live = false, raf = 0, last = 0;

      function size() {
        var r = cv.getBoundingClientRect();
        w = Math.max(1, Math.ceil(r.width / PX));
        h = Math.max(1, Math.ceil(r.height / PX));
        cv.width = w; cv.height = h;
        img = ctx.createImageData(w, h);
      }

      function frame(now) {
        if (!live) return;
        raf = requestAnimationFrame(frame);
        if (now - last < 55) return;   // ~18fps: the chunky cadence is the point
        last = now;
        var t = now / 1000, d = img.data, i = 0;
        for (var y = 0; y < h; y++) {
          var ny = y / h;
          for (var x = 0; x < w; x++) {
            var v = field(x / w, ny, t);
            var thr = B[(y & 7) * 8 + (x & 7)];
            var on = v > thr;
            d[i] = RGB[0]; d[i + 1] = RGB[1]; d[i + 2] = RGB[2];
            d[i + 3] = on ? Math.min(220, 55 + v * 170) : 0;
            i += 4;
          }
        }
        ctx.putImageData(img, 0, 0);
      }

      size();
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          live = e.isIntersecting;
          if (live) { last = 0; cancelAnimationFrame(raf); raf = requestAnimationFrame(frame); }
          else cancelAnimationFrame(raf);
        });
      }, { rootMargin: '120px' });
      io.observe(cv);

      var rt;
      window.addEventListener('resize', function () {
        clearTimeout(rt);
        rt = setTimeout(size, 180);
      }, { passive: true });
    });
  });

  /* ══ 2. custom cursor ══════════════════════════════════════ */
  run(function () {
    if (!fine || reduced) return;
    var el = $('#cursor');
    if (!el) return;
    document.documentElement.classList.add('has-cursor');
    el.style.opacity = '0';   // no phantom square before the pointer has moved

    var tx = window.innerWidth / 2, ty = window.innerHeight / 2, cx = tx, cy = ty, raf = 0;

    function tick() {
      cx = lerp(cx, tx, 0.22);
      cy = lerp(cy, ty, 0.22);
      el.style.transform = 'translate3d(' + cx + 'px,' + cy + 'px,0)';
      raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);

    window.addEventListener('mousemove', function (e) {
      if (el.style.opacity === '0') { cx = tx = e.clientX; cy = ty = e.clientY; el.style.opacity = '1'; }
      tx = e.clientX; ty = e.clientY;
    }, { passive: true });
    window.addEventListener('mousedown', function () { el.classList.add('down'); });
    window.addEventListener('mouseup', function () { el.classList.remove('down'); });
    document.addEventListener('mouseleave', function () { el.style.opacity = '0'; });
    document.addEventListener('mouseenter', function () { el.style.opacity = '1'; });

    var HOT = 'a,button,summary,.cell,.tier,.sat,.chip,input,select';
    document.addEventListener('mouseover', function (e) {
      if (e.target.closest && e.target.closest(HOT)) el.classList.add('hot');
    });
    document.addEventListener('mouseout', function (e) {
      if (e.target.closest && e.target.closest(HOT)) el.classList.remove('hot');
    });
  });

  /* ══ 3. scroll progress + nav state + active link ══════════ */
  run(function () {
    var bar = $('#progress');
    var nav = $('#nav');
    var links = $$('.nav-mid a[href^="#"]');
    var targets = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
    var ticking = false;

    function paint() {
      ticking = false;
      var y = window.scrollY;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      if (bar) bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, y / max) : 0) + ')';
      if (nav) nav.classList.toggle('stuck', y > 24);

      var mid = y + window.innerHeight * 0.34, best = -1;
      targets.forEach(function (t, i) { if (t && t.offsetTop <= mid) best = i; });
      links.forEach(function (a, i) { a.classList.toggle('on', i === best); });
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(paint); }
    }, { passive: true });
    paint();
  });

  /* ══ 4. mobile menu ════════════════════════════════════════ */
  run(function () {
    var b = $('#burger'), m = $('#navMid');
    if (!b || !m) return;
    var close = function () { m.classList.remove('open'); b.setAttribute('aria-expanded', 'false'); };
    b.addEventListener('click', function () {
      var open = m.classList.toggle('open');
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    m.addEventListener('click', function (e) { if (e.target.closest('a')) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  });

  /* ══ 5. hero terminal typing ═══════════════════════════════ */
  run(function () {
    var out = $('#termT');
    if (!out) return;
    var lines = [
      'leon --services | wc -l   → 35',
      'leon --quote "booking system"',
      'leon --stack ios android web ai',
      'leon --owns-the-code you'
    ];
    if (reduced) { out.textContent = lines[0]; return; }

    var li = 0, ci = 0, dir = 1;
    (function step() {
      var full = lines[li];
      ci += dir;
      out.textContent = full.slice(0, ci);
      var wait = dir > 0 ? 42 : 22;
      if (dir > 0 && ci >= full.length) { dir = -1; wait = 2100; }
      else if (dir < 0 && ci <= 0) { dir = 1; li = (li + 1) % lines.length; wait = 320; }
      setTimeout(step, wait);
    })();
  });

  /* ══ 6. text scramble on reveal ════════════════════════════
     Scrambling writes textContent, which would delete any <em>
     inside a heading. So a mixed heading is split into its parts
     first — bare text wrapped in a span, elements left alone —
     and each part scrambles on its own. The markup survives. */
  var CH = '#$%&*+-<>[]{}/\\=_01';

  function scrambleLeaf(el, delay) {
    var text = el.getAttribute('data-text') || el.textContent;
    el.setAttribute('data-text', text);
    var frame = -Math.round(delay / 16), queue = [], t0 = Date.now(), settledOut = false;
    for (var i = 0; i < text.length; i++) {
      queue.push({ ch: text[i], start: Math.floor(Math.random() * 12), end: Math.floor(Math.random() * 12) + 14 + i * 0.6 });
    }
    /* belt and braces: rAF can be paused outright (background tab), and a
       heading left as random glyphs is worse than no effect at all. */
    setTimeout(function () { if (!settledOut) { settledOut = true; el.textContent = text; } }, 2200 + delay);
    (function tick() {
      /* hard stop: if rAF is throttled (background tab, headless, slow device)
         the effect must never leave a heading as garbage. */
      if (Date.now() - t0 > 1800) { el.textContent = text; return; }
      if (frame < 0) { frame++; requestAnimationFrame(tick); return; }
      var out = '', settled = 0;
      for (var i = 0; i < queue.length; i++) {
        var q = queue[i];
        if (frame >= q.end || q.ch === ' ') { out += q.ch; settled++; }
        else if (frame >= q.start) { out += CH[(Math.random() * CH.length) | 0]; }
        else { out += ' '; }
      }
      el.textContent = out;
      if (settled === queue.length) return;
      frame++;
      requestAnimationFrame(tick);
    })();
  }

  function parts(el) {
    var out = [], kids = Array.prototype.slice.call(el.childNodes), has = false;
    kids.forEach(function (n) {
      if (n.nodeType === 1 && n.tagName !== 'BR') has = true;
    });
    if (!has) return [el];
    kids.forEach(function (n) {
      if (n.nodeType === 3) {
        if (!n.textContent.trim()) return;
        var s = document.createElement('span');
        s.textContent = n.textContent;
        el.replaceChild(s, n);
        out.push(s);
      } else if (n.nodeType === 1 && n.tagName !== 'BR') {
        out.push(n);
      }
    });
    return out.length ? out : [el];
  }

  run(function () {
    if (reduced || !('IntersectionObserver' in window)) return;
    var els = $$('[data-scramble]');
    if (!els.length) return;
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        parts(e.target).forEach(function (p, i) { scrambleLeaf(p, i * 90); });
      });
    }, { threshold: 0.35 });
    els.forEach(function (el) { io.observe(el); });
  });

  /* ══ 7. reveal on scroll ═══════════════════════════════════ */
  run(function () {
    if (!('IntersectionObserver' in window) || reduced) return;

    var groups = [
      '.sec-head', '.chips', '.cell', '.row', '.steps li', '.tier',
      '.faq details', '.facts li', '.rowsx', '.hero-facts', '.term', '.hero-cta',
      '.more', '.tnote', '.foot-in > *'
    ];
    var els = [];
    groups.forEach(function (sel) { els = els.concat($$(sel)); });
    if (!els.length) return;

    document.documentElement.classList.add('js');
    els.forEach(function (el, i) {
      el.setAttribute('data-rise', '');
      el.style.transitionDelay = ((i % 5) * 55) + 'ms';
    });

    var reveal = function (el) { el.classList.add('in'); };
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        reveal(e.target);
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.05 });
    els.forEach(function (el) { io.observe(el); });

    // failsafe: nothing stays invisible, whatever happens above
    setTimeout(function () { els.forEach(reveal); }, 3000);
  });

  /* ══ 8. counters ═══════════════════════════════════════════ */
  run(function () {
    if (!('IntersectionObserver' in window)) return;
    var els = $$('[data-count]');
    if (!els.length) return;

    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target, end = parseInt(el.getAttribute('data-count'), 10) || 0;
        if (reduced) { el.textContent = end.toLocaleString('en-US'); return; }
        var t0 = 0, dur = 1250;
        (function step(now) {
          if (!t0) t0 = now;
          var p = Math.min(1, (now - t0) / dur);
          var e2 = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(end * e2).toLocaleString('en-US');
          if (p < 1) requestAnimationFrame(step);
        })(0);
      });
    }, { threshold: 0.6 });
    els.forEach(function (el) { io.observe(el); });
  });

  /* ══ 9. magnetic buttons ═══════════════════════════════════ */
  run(function () {
    if (!fine || reduced) return;
    $$('.magnet').forEach(function (el) {
      var raf = 0, tx = 0, ty = 0, cx = 0, cy = 0, on = false;
      function tick() {
        cx = lerp(cx, tx, 0.18); cy = lerp(cy, ty, 0.18);
        el.style.transform = 'translate(' + cx.toFixed(2) + 'px,' + cy.toFixed(2) + 'px)';
        if (on || Math.abs(cx) > 0.1 || Math.abs(cy) > 0.1) raf = requestAnimationFrame(tick);
        else { el.style.transform = ''; raf = 0; }
      }
      el.addEventListener('mouseenter', function () { on = true; if (!raf) raf = requestAnimationFrame(tick); });
      el.addEventListener('mousemove', function (e) {
        var r = el.getBoundingClientRect();
        tx = (e.clientX - (r.left + r.width / 2)) * 0.28;
        ty = (e.clientY - (r.top + r.height / 2)) * 0.34;
      });
      el.addEventListener('mouseleave', function () { on = false; tx = 0; ty = 0; });
    });
  });

  /* ══ 10. spotlight on service cells ════════════════════════ */
  run(function () {
    if (!fine || reduced) return;
    var grid = $('#grid');
    if (!grid) return;
    grid.addEventListener('mousemove', function (e) {
      var cell = e.target.closest ? e.target.closest('.cell') : null;
      if (!cell) return;
      var r = cell.getBoundingClientRect();
      cell.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      cell.style.setProperty('--my', (e.clientY - r.top) + 'px');
    }, { passive: true });
  });

  /* ══ 11. service filters ═══════════════════════════════════ */
  run(function () {
    var chips = $$('.chip[data-filter]');
    var cells = $$('.cell[data-cat]');
    var note = $('#gridnote');
    if (!chips.length || !cells.length) return;

    var names = { all: '', web: 'web & apps', ai: 'ai', ops: 'automation', growth: 'growth', data: 'data' };

    function pick(key) {
      var shown = 0;
      cells.forEach(function (c) {
        var match = key === 'all' || (c.getAttribute('data-cat') || '').split(/\s+/).indexOf(key) !== -1;
        c.hidden = !match;
        if (match) shown++;
      });
      chips.forEach(function (c) {
        var on = c.getAttribute('data-filter') === key;
        c.classList.toggle('on', on);
        c.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      if (note) {
        note.hidden = key === 'all';
        if (key !== 'all') note.textContent = '// ' + shown + ' in ' + names[key] + ' — most jobs combine several';
      }
    }

    chips.forEach(function (chip) {
      chip.addEventListener('click', function () { pick(chip.getAttribute('data-filter')); });
      chip.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        e.preventDefault();
        var i = chips.indexOf(chip) + (e.key === 'ArrowRight' ? 1 : -1);
        var next = chips[(i + chips.length) % chips.length];
        next.focus(); pick(next.getAttribute('data-filter'));
      });
    });
  });

  /* ══ 12. marquee: duplicate the track so the loop is seamless ══ */
  run(function () {
    var track = $('#marq .marq-t');
    if (!track || reduced) return;
    track.innerHTML += track.innerHTML;
  });

  /* ══ 13. footer year ═══════════════════════════════════════ */
  run(function () {
    var y = $('#yr');
    if (y) y.textContent = String(new Date().getFullYear());
  });

})();
