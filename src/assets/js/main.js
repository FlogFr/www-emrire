// Menu mobile + ombre de l'en-tête au défilement. Le site reste utilisable sans JavaScript.
(function () {
  var header = document.querySelector('.site-header');
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('menu-principal');

  function setOpen(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.querySelector('.sr-only').textContent = open ? 'Fermer le menu' : 'Ouvrir le menu';
    nav.classList.toggle('is-open', open);
  }

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }
})();
