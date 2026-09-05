/* Homepage-inspired depth, without a framework or delayed access to content. */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)');
  var cleanups = [];
  var frame = 0;
  function reset() {
    cancelAnimationFrame(frame); frame = 0;
    cleanups.splice(0).forEach(function (fn) { fn(); });
    document.querySelectorAll('.lb-arrive,.lb-motion-frame,.lb-tilting').forEach(function (el) {
      el.classList.remove('lb-arrive','lb-motion-frame','lb-tilting');
      el.style.removeProperty('--lb-rx'); el.style.removeProperty('--lb-ry');
    });
  }
  function start() {
    reset();
    if (reduce.matches || !('IntersectionObserver' in window)) return;
    var cards = Array.from(document.querySelectorAll('.cell,.fixcard,.buyer-proof-card,.row-art,.case-hero-media,.service-proof-media,.testimonial-card,.offer-card'))
      .filter(function (el) { return !el.closest('form,.call-page,.quote-page,.as-panel') && !el.querySelector('form,input,textarea,iframe'); });
    var entering = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('lb-arrive');
        entry.target.addEventListener('animationend',function done() {
          entry.target.classList.remove('lb-arrive');
          entry.target.removeEventListener('animationend',done);
        });
        entering.unobserve(entry.target);
      });
    },{threshold:0.08});
    var revealTargets = Array.from(document.querySelectorAll('.sec-head,.page-section-title,.foot-in > *, .row-txt'));
    revealTargets.concat(cards).forEach(function (el) {
      if (el.getBoundingClientRect().top > window.innerHeight * 0.85) entering.observe(el);
    });
    cleanups.push(function () { entering.disconnect(); });
    if (fine.matches) cards.forEach(function (el) {
      el.classList.add('lb-motion-frame');
      var raf = 0;
      function move(event) {
        if (document.hidden || el.matches(':focus-within')) return;
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(function () {
          var rect = el.getBoundingClientRect();
          var x = Math.max(-.5,Math.min(.5,(event.clientX-rect.left)/rect.width-.5));
          var y = Math.max(-.5,Math.min(.5,(event.clientY-rect.top)/rect.height-.5));
          el.classList.add('lb-tilting');
          el.style.setProperty('--lb-rx',(-y*7).toFixed(2)+'deg');
          el.style.setProperty('--lb-ry',(x*9).toFixed(2)+'deg');
        });
      }
      function leave() { cancelAnimationFrame(raf); el.classList.remove('lb-tilting'); el.style.removeProperty('--lb-rx'); el.style.removeProperty('--lb-ry'); }
      el.addEventListener('pointermove',move,{passive:true}); el.addEventListener('pointerleave',leave); el.addEventListener('focusin',leave);
      cleanups.push(function () { leave(); el.removeEventListener('pointermove',move); el.removeEventListener('pointerleave',leave); el.removeEventListener('focusin',leave); });
    });
    // Native scroll progress uses the existing accessible page and its actual height.
    var hero = document.querySelector('.page-hero .rail');
    var track = hero && hero.querySelector('.lb-section-track');
    if (hero && !track) { track=document.createElement('div'); track.className='lb-section-track'; track.setAttribute('aria-hidden','true'); hero.appendChild(track); }
    function paint() { frame=0; if (!track) return; var max=document.documentElement.scrollHeight-window.innerHeight;
      track.style.setProperty('--lb-progress',(max>0?Math.min(100,Math.max(0,window.scrollY/max*100)):100)+'%'); }
    function scroll() { if (!frame && !document.hidden) frame=requestAnimationFrame(paint); }
    window.addEventListener('scroll',scroll,{passive:true}); window.addEventListener('resize',scroll,{passive:true}); paint();
    cleanups.push(function () { window.removeEventListener('scroll',scroll); window.removeEventListener('resize',scroll); if(track)track.remove(); });
  }
  reduce.addEventListener('change',start); fine.addEventListener('change',start);
  document.addEventListener('visibilitychange',function () { if(document.hidden)reset();else start(); });
  start();
}());

/* Short, replayable examples. They never call an API or send a form. */
(function () {
  'use strict';
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)');
  var timers=new Map();
  function stop(scene) {
    if(timers.has(scene))clearTimeout(timers.get(scene)); timers.delete(scene);
    scene.classList.remove('is-playing');
  }
  function play(scene,announce) {
    stop(scene);
    var feedback=scene.querySelector('.flow-feedback');
    if(feedback)feedback.textContent='';
    if(reduce.matches) { if(announce&&feedback)feedback.textContent=feedback.dataset.complete; return; }
    // Force only this tiny illustration to restart; no continuous render loop.
    void scene.offsetWidth;
    scene.classList.add('is-playing');
    timers.set(scene,setTimeout(function () {
      stop(scene); if(announce&&feedback)feedback.textContent=feedback.dataset.complete;
    },3200));
  }
  document.querySelectorAll('[data-flow]').forEach(function (scene) {
    var button=scene.querySelector('[data-flow-play]');
    if(button) { button.addEventListener('click',function () { play(scene,true); }); button.hidden=false; }
  });
  document.querySelectorAll('.visual-chooser').forEach(function (chooser) {
    function select(animate) {
      var selected=chooser.querySelector('input[name="build-choice"]:checked');
      if(!selected)return;
      chooser.querySelectorAll('[data-choice-panel]').forEach(function (panel) {
        panel.hidden=panel.dataset.choicePanel!==selected.value;
        panel.querySelectorAll('[data-flow]').forEach(function (scene) {
          stop(scene); if(!panel.hidden&&animate)play(scene,false);
        });
      });
    }
    chooser.addEventListener('change',function () { select(true); }); select(false);
  });
  if('IntersectionObserver' in window&&!reduce.matches) {
    var entered=new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if(document.hidden||!entry.isIntersecting||entry.target.closest('[hidden]'))return;
        play(entry.target,false); entered.unobserve(entry.target);
      });
    },{threshold:.35});
    document.querySelectorAll('[data-flow]').forEach(function (scene) { entered.observe(scene); });
    // Keep unseen scenes observed across tab switches; callbacks are quiet when hidden.
  }
  function stopAll() { Array.from(timers.keys()).forEach(stop); }
  reduce.addEventListener('change',stopAll);
  document.addEventListener('visibilitychange',function () { if(document.hidden)stopAll(); });
  window.addEventListener('pagehide',stopAll);
  function revealAnchor() {
    if(!location.hash)return;
    var target;
    try { target=document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch(_) { return; }
    if(!target)return;
    var parent=target.parentElement;
    while(parent) { if(parent.tagName==='DETAILS')parent.open=true; parent=parent.parentElement; }
  }
  window.addEventListener('hashchange',revealAnchor); revealAnchor();
}());
