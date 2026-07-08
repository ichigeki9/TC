// ===== HAMBURGER MENU =====
const hamburger = document.querySelector('.hamburger');
const mobileMenu = document.querySelector('.mobile-menu');

hamburger?.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  mobileMenu.classList.toggle('open');
  document.body.style.overflow = mobileMenu.classList.contains('open') ? 'hidden' : '';
});

// Mobile submenu toggles
document.querySelectorAll('.mobile-nav-link[data-toggle]').forEach(link => {
  link.addEventListener('click', () => {
    const targetId = link.dataset.toggle;
    const submenu = document.getElementById(targetId);
    submenu?.classList.toggle('open');
    const arrow = link.querySelector('.m-arrow');
    if (arrow) arrow.style.transform = submenu?.classList.contains('open') ? 'rotate(90deg)' : '';
  });
});

// ===== COOKIE BANNER =====
const cookieBanner = document.getElementById('cookieBanner');

if (!localStorage.getItem('tc_cookie_consent')) {
  setTimeout(() => cookieBanner?.classList.add('show'), 1200);
}

document.getElementById('cookieAccept')?.addEventListener('click', () => {
  localStorage.setItem('tc_cookie_consent', 'accepted');
  cookieBanner?.classList.remove('show');
});

document.getElementById('cookieDecline')?.addEventListener('click', () => {
  localStorage.setItem('tc_cookie_consent', 'declined');
  cookieBanner?.classList.remove('show');
});

// ===== NEWSLETTER FORM =====
const newsletterForm = document.getElementById('newsletterForm');
newsletterForm?.addEventListener('submit', (e) => {
  e.preventDefault();
  const input = newsletterForm.querySelector('input[type="email"]');
  const btn = newsletterForm.querySelector('.newsletter-submit');
  const originalText = btn.textContent;

  btn.textContent = 'Zapisano!';
  btn.style.background = '#4ade80';
  input.value = '';

  setTimeout(() => {
    btn.textContent = originalText;
    btn.style.background = '';
  }, 3000);
});

// ===== SCROLL ANIMATIONS =====
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -60px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll('.animate-in').forEach(el => observer.observe(el));

// ===== TESTIMONIALS DUPLICATE (for infinite scroll) =====
const track = document.querySelector('.testimonials-track');
if (track) {
  const clone = track.innerHTML;
  track.innerHTML += clone;
}

// ===== HEADER SCROLL EFFECT =====
const header = document.querySelector('header');
let lastScrollY = window.scrollY;

window.addEventListener('scroll', () => {
  const currentScrollY = window.scrollY;

  if (currentScrollY > 80) {
    header?.classList.add('scrolled');
  } else {
    header?.classList.remove('scrolled');
  }

  lastScrollY = currentScrollY;
}, { passive: true });

// ===== ACTIVE NAV LINK =====
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-link[data-section]');

const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.id;
      navLinks.forEach(link => {
        link.classList.toggle('active', link.dataset.section === id);
      });
    }
  });
}, { threshold: 0.4 });

sections.forEach(section => sectionObserver.observe(section));
