/* ============================================================
   BORIS — черновик сайта (issue #5)
   Небольшой vanilla JS: мобильное меню, мягкое появление блоков,
   лайтбокс для фотографий. Без внешних библиотек.
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 1. Мобильное меню ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('is-open', !open);
      toggle.setAttribute('aria-label', open ? 'Открыть меню' : 'Закрыть меню');
    });
    // по клику по пункту — закрывать меню
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) {
        toggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-label', 'Открыть меню');
      }
    });
  }

  /* ---------- 2. Появление блоков при прокрутке ---------- */
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var reveals = document.querySelectorAll('.reveal');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveals.forEach(function (el) { io.observe(el); });
  }

  /* ---------- 3. Лайтбокс (открывается по клику на фото работ) ---------- */
  var lightbox = document.getElementById('lightbox');
  if (!lightbox) return;

  var lbImg = lightbox.querySelector('.lightbox__img');
  var lbCaption = lightbox.querySelector('.lightbox__caption');
  var lbClose = lightbox.querySelector('.lightbox__close');
  var lastFocused = null;

  // кликаемы только кадры галерей/кейсов — фигуры внутри секции работ и направлений
  var figures = document.querySelectorAll('.case__figure, .direction-card figure, .approach__figure');

  function openLightbox(img) {
    lastFocused = document.activeElement;
    lbImg.src = img.currentSrc || img.src;
    lbImg.alt = img.alt || '';
    // подпись: берём текст из figcaption/заголовка кейса, если есть
    var article = img.closest('.case');
    var caption = '';
    if (article) {
      var h = article.querySelector('.case__caption h3');
      var p = article.querySelector('.case__caption p');
      caption = (h ? h.textContent.trim() : '') + (p ? ' — ' + p.textContent.trim() : '');
    } else {
      caption = img.alt || '';
    }
    lbCaption.textContent = caption;
    lightbox.hidden = false;
    document.body.style.overflow = 'hidden';
    lbClose.focus();
  }

  function closeLightbox() {
    lightbox.hidden = true;
    lbImg.src = '';
    document.body.style.overflow = '';
    if (lastFocused) lastFocused.focus();
  }

  figures.forEach(function (fig) {
    var img = fig.querySelector('img');
    if (!img) return;
    fig.style.cursor = 'zoom-in';
    fig.setAttribute('tabindex', '0');
    fig.setAttribute('role', 'button');
    fig.setAttribute('aria-label', 'Увеличить: ' + (img.alt || 'фотография'));
    fig.addEventListener('click', function () { openLightbox(img); });
    fig.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openLightbox(img);
      }
    });
  });

  lbClose.addEventListener('click', closeLightbox);
  lightbox.addEventListener('click', function (e) {
    if (e.target === lightbox) closeLightbox();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !lightbox.hidden) closeLightbox();
  });
})();
