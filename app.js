/* Leon Dev — site behaviour.
   Every feature is isolated in its own try/catch on purpose: a throw in one
   must never take the rest of the page down with it. Content is visible by
   default; JS only ever *adds* enhancement. */

(function () {
  'use strict';

  var run = function (fn) { try { fn(); } catch (e) { /* fail soft */ } };

  /* ── sticky nav ─────────────────────────────────────────── */
  run(function () {
    var nav = document.getElementById('nav');
    if (!nav) return;
    var apply = function () { nav.classList.toggle('stuck', window.scrollY > 12); };
    apply();
    window.addEventListener('scroll', apply, { passive: true });
  });

  /* ── mobile menu ────────────────────────────────────────── */
  run(function () {
    var btn = document.getElementById('navToggle');
    var links = document.getElementById('navLinks');
    if (!btn || !links) return;

    var close = function () {
      links.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
    };

    btn.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    links.addEventListener('click', function (e) {
      if (e.target.closest('a')) close();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
  });

  /* ── service filters ────────────────────────────────────── */
  run(function () {
    var chips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-filter]'));
    var cards = Array.prototype.slice.call(document.querySelectorAll('.svc[data-cat]'));
    var note = document.getElementById('svcNote');
    if (!chips.length || !cards.length) return;

    var labels = {
      all: '', web: 'Web & Apps', ai: 'AI Systems',
      ops: 'Automation & Ops', growth: 'Growth & Content', data: 'Data & Intelligence'
    };

    var select = function (key) {
      var shown = 0;
      cards.forEach(function (card) {
        var cats = (card.getAttribute('data-cat') || '').split(/\s+/);
        var match = key === 'all' || cats.indexOf(key) !== -1;
        card.hidden = !match;
        if (match) shown++;
      });
      chips.forEach(function (chip) {
        var on = chip.getAttribute('data-filter') === key;
        chip.classList.toggle('is-on', on);
        chip.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      if (note) {
        if (key === 'all') {
          note.hidden = true;
        } else {
          note.hidden = false;
          note.textContent = shown + ' service' + (shown === 1 ? '' : 's') + ' in ' + labels[key] +
            ' — most builds combine several.';
        }
      }
    };

    chips.forEach(function (chip) {
      chip.addEventListener('click', function () { select(chip.getAttribute('data-filter')); });
      chip.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        e.preventDefault();
        var i = chips.indexOf(chip) + (e.key === 'ArrowRight' ? 1 : -1);
        var next = chips[(i + chips.length) % chips.length];
        next.focus();
        select(next.getAttribute('data-filter'));
      });
    });
  });

  /* ── scroll reveal ──────────────────────────────────────── */
  run(function () {
    if (!('IntersectionObserver' in window)) return;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var targets = Array.prototype.slice.call(document.querySelectorAll(
      '.sec-head, .hero-panel, .svc-grid, .filters, .work, .steps, .tier, .faq, .ind, .facts, .contact-rows, .cta-circle, .script-head'
    ));
    if (!targets.length) return;

    document.documentElement.classList.add('js');
    targets.forEach(function (el, i) {
      el.setAttribute('data-rise', '');
      el.style.transitionDelay = (Math.min(i % 4, 3) * 60) + 'ms';
    });

    var reveal = function (el) { el.classList.add('in'); };

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        reveal(entry.target);
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });

    targets.forEach(function (el) { io.observe(el); });

    /* failsafe: nothing stays invisible, whatever happens above */
    window.setTimeout(function () { targets.forEach(reveal); }, 2600);
  });

  /* ── footer year ────────────────────────────────────────── */
  run(function () {
    var yr = document.getElementById('yr');
    if (yr) yr.textContent = String(new Date().getFullYear());
  });

})();
