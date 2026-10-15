/* Progressive enhancements: HTML carries every locale, source and download link. */
(() => {
  'use strict';
  const root = document.documentElement;
  const dark = matchMedia('(prefers-color-scheme: dark)');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const theme = document.querySelector('#theme');
  const read = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const save = (key, value) => { try { localStorage.setItem(key, value); } catch { /* Storage can be unavailable in private sessions. */ } };
  let preference = read('spaceneeded-theme');
  if (!['light', 'dark', 'system'].includes(preference)) preference = 'system';
  function applyTheme() {
    root.dataset.theme = preference;
    theme.value = preference;
    const appearance = preference === 'system' ? (dark.matches ? 'dark' : 'light') : preference;
    document.querySelectorAll('source[data-dark]').forEach(source => source.media = appearance === 'dark' ? 'all' : 'not all');
  }
  theme.addEventListener('change', () => { preference = theme.value; save('spaceneeded-theme', preference); applyTheme(); });
  dark.addEventListener('change', applyTheme);
  applyTheme();

  const language = document.querySelector('.language');
  document.addEventListener('click', event => { if (!language.contains(event.target)) language.open = false; });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && language.open) { language.open = false; language.querySelector('summary').focus(); } });

  const motion = document.querySelector('#motion');
  let paused = read('spaceneeded-motion') === 'paused';
  let offscreen = false;
  function applyMotion() {
    const stopped = paused || reduced.matches;
    root.classList.toggle('motion-paused', stopped || document.hidden);
    root.classList.toggle('ambient-offscreen', offscreen);
    motion.hidden = reduced.matches;
    motion.setAttribute('aria-pressed', String(paused));
    motion.querySelector('[data-motion-label]').textContent = paused ? motion.dataset.resume : motion.dataset.pause;
    motion.querySelector('[aria-hidden]').textContent = paused ? '▷' : 'Ⅱ';
    if (reduced.matches) document.querySelectorAll('[data-reveal]').forEach(element => element.dataset.reveal = 'visible');
  }
  motion.addEventListener('click', () => { paused = !paused; save('spaceneeded-motion', paused ? 'paused' : 'playing'); applyMotion(); });
  reduced.addEventListener('change', applyMotion);
  document.addEventListener('visibilitychange', applyMotion);
  applyMotion();

  if ('IntersectionObserver' in window) {
    const ambient = new IntersectionObserver(entries => { offscreen = !entries[0].isIntersecting; applyMotion(); });
    ambient.observe(document.querySelector('.arc-atmosphere'));
    const reveals = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.dataset.reveal = 'visible'; reveals.unobserve(entry.target); }
    }), { rootMargin: '0px 0px -40px 0px', threshold: 0.05 });
    if (!reduced.matches) document.querySelectorAll('.reveal').forEach(element => {
      // Never hide initially visible content, including deep-linked sections.
      if (element.getBoundingClientRect().top > innerHeight) {
        element.dataset.reveal = 'pending';
        reveals.observe(element);
      }
    });
    // Keyboard navigation should never land in an invisible reveal section.
    document.addEventListener('focusin', event => {
      const section = event.target.closest('[data-reveal]');
      if (section) { section.style.transition = 'none'; section.dataset.reveal = 'visible'; reveals.unobserve(section); }
    });
  }
})();
