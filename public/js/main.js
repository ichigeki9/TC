// ===== EXTERNAL LINKS (sklep, plany) =====
// Dopóki adres w js/config.js jest pusty, link zostaje przy swoim href (kotwica na stronie).
document.querySelectorAll('[data-link]').forEach(link => {
  const base = typeof TC_LINKS !== 'undefined' ? TC_LINKS[link.dataset.link] : '';
  if (!base) return;
  link.href = link.dataset.path ? base.replace(/\/$/, '') + link.dataset.path : base;
  link.target = '_blank';
  link.rel = 'noopener';
});

// ===== HAMBURGER MENU =====
const hamburger = document.querySelector('.hamburger');
const mobileMenu = document.querySelector('.mobile-menu');

hamburger?.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  mobileMenu.classList.toggle('open');
  document.body.style.overflow = mobileMenu.classList.contains('open') ? 'hidden' : '';
});

// Zamknij menu po kliknięciu linku (m.in. kotwice na tej samej stronie)
mobileMenu?.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    hamburger?.classList.remove('open');
    mobileMenu.classList.remove('open');
    document.body.style.overflow = '';
  });
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

// ===== PROGRAM MODAL =====
const programData = [
  {
    icon: '🏋️',
    tag: 'Bestseller',
    title: 'CrossFit',
    lead: 'Kompleksowy trening funkcjonalny łączący siłę, wytrzymałość i ruch atletyczny. Każdy dzień przynosi nowe wyzwanie.',
    contents: [
      'Codzienne WODy (Workout of the Day)',
      'Trening siłowy: przysiad, martwy ciąg, wyciskanie',
      'Elementy gimnastyki i ruchów olimpijskich',
      'Cardio: wiosłowanie, biegi, skipping',
      'Skale trudności dla każdego poziomu',
    ],
    forWho: 'Dla osób szukających wszechstronności — od kompletnych początkujących po zaawansowanych zawodników. Program skaluje się do Twojego poziomu.',
    whyFor: 'CrossFit buduje ciało gotowe na wszystko. Poprawia siłę, kondycję, mobilność i skład ciała jednocześnie — bez monotonii i rutyny.',
  },
  {
    icon: '⚡',
    tag: 'Nowość',
    title: 'Hybrydowy',
    lead: 'Połączenie treningu siłowego z bieganiem — dwa światy w jednym programie. Bądź silny I szybki naraz.',
    contents: [
      '3–4 sesje siłowe tygodniowo (squat, deadlift, press)',
      '2–3 sesje biegowe z różnymi strefami tętna',
      'Planowanie żywienia pod podwójny wysiłek',
      'Strategia regeneracji i tapering',
      'Testy wynikowe co 4 tygodnie',
    ],
    forWho: 'Dla sportowców, którzy nie chcą wybierać między siłownią a bieganiem. Idealny dla osób przygotowujących się do zawodów typu Hyrox lub triatlon.',
    whyFor: 'Trening hybrydowy to przyszłość sportu amatorskiego. Poprawia zarówno wyniki siłowe, jak i wytrzymałościowe bez poświęcania jednego dla drugiego.',
  },
  {
    icon: '🔥',
    tag: 'Popularny',
    title: 'Hyrox',
    lead: 'Specjalistyczne przygotowanie do zawodów Hyrox — 8 stacji, 8 km biegu, jeden wynik. Trenuj jak zawodowiec.',
    contents: [
      'Symulacje zawodów Hyrox (SkiErg, Wall Balls, Sandbag Lunges…)',
      'Trening progowy i interwałowy',
      'Siła funkcjonalna pod specyficzne stacje',
      'Planowanie startu i strategia tempa',
      'Analiza wyników i korekty planu',
    ],
    forWho: 'Dla osób planujących start w zawodach Hyrox lub chcących sprawdzić się w ustrukturyzowanym wyzwaniu fitness. Wymaga bazy kondycyjnej.',
    whyFor: 'Hyrox to jeden z najszybciej rosnących formatów zawodniczych na świecie. Program przygotowuje Cię do rywalizacji, ale efekty widać w codziennym treningu.',
  },
  {
    icon: '💪',
    tag: 'Klasyk',
    title: 'Trening Siłowy',
    lead: 'Powrót do podstaw. Przysiad, martwy ciąg, wyciskanie — trzy ruchy, które zmieniają ciało. Bez zbędnych komplikacji.',
    contents: [
      'Periodyzacja liniowa i falowa',
      'Techniczne opanowanie Big 3: squat, deadlift, bench press',
      'Trening pomocniczy pod słabe ogniwa',
      'Testy maksymalne co blok treningowy',
      'Wskazówki techniczne z wideo',
    ],
    forWho: 'Dla każdego, kto chce być silniejszy. Od osób stawiających pierwsze kroki z ciężarami po doświadczonych siłaczy szukających nowego bodźca.',
    whyFor: 'Siła bazowa przekłada się na wszystko — lepsze wyniki w sporcie, zdrowsze stawy, lepsza sylwetka i wyższa jakość życia z wiekiem.',
  },
  {
    icon: '🤸',
    tag: '',
    title: 'Gimnastyka',
    lead: 'Panowanie nad własnym ciałem to prawdziwa siła. Naucz się ruchów, które wyglądają jak magia — i poczuj co naprawdę możesz zrobić.',
    contents: [
      'Podciąganie: od zera do zaawansowanych variant',
      'Muscle-up na drążku i kółkach',
      'Handstand walk i statyka na rękach',
      'Ćwiczenia na kółkach gimnastycznych',
      'Progresje krok po kroku dla każdego ruchu',
    ],
    forWho: 'Dla osób chcących opanować ruchy ciężarem własnego ciała — niezależnie czy startują od zera, czy chcą dodać gimnastykę do swojego CrossFitu.',
    whyFor: 'Gimnastyka poprawia siłę względną, propriocepcję i kontrolę ciała. Efekty widać natychmiast w każdej innej dyscyplinie sportowej.',
  },
  {
    icon: '🏅',
    tag: '',
    title: 'Weightlifting',
    lead: 'Rwanie i podrzut — dwa ruchy, nieskończone możliwości. Olimpijska sztanga uczy cierpliwości, techniki i eksplozywności.',
    contents: [
      'Technika rwania od podstaw do zawansowanego poziomu',
      'Technika podrzutu: dip & drive, jerk',
      'Ćwiczenia pomocnicze: snatch pull, clean pull, overhead squat',
      'Mobilność pod wymogi bojów olimpijskich',
      'Planowanie startów zawodniczych',
    ],
    forWho: 'Dla osób zafascynowanych bojami olimpijskimi — od zupełnych nowicjuszy po zawodników CrossFit chcących podnieść swoje lifty.',
    whyFor: 'Weightlifting buduje eksplozywność, koordynację i siłę, których nie osiągniesz żadną inną metodą. To technicznie najbardziej wymagająca dyscyplina siłowa.',
  },
  {
    icon: '🧘',
    tag: '',
    title: 'Mobility',
    lead: 'Zakres ruchu to inwestycja na całe życie. Pracuj nad elastycznością, mobilnością stawów i jakością ruchu — dziś i za 30 lat.',
    contents: [
      'Rutyny poranne i wieczorne (10–30 min)',
      'Praca nad biodrem, barkiem, klatką i kostką',
      'Stretching dynamiczny i statyczny',
      'Techniki fascial release i oddechowe',
      'Mobilność specyficzna pod wybrane dyscypliny',
    ],
    forWho: 'Dla każdego — od zawodników z ograniczeniami ruchowymi po osoby siedzące przy biurku. Mobility można i trzeba trenować niezależnie od poziomu.',
    whyFor: 'Większy zakres ruchu = lepsza technika = mniejsze ryzyko kontuzji = lepsze wyniki. To najprostsza inwestycja z najszerszym zwrotem.',
  },
  {
    icon: '🩺',
    tag: '',
    title: 'Rehab',
    lead: 'Kontuzja to nie koniec. To moment, żeby wrócić mądrzej, silniej i z lepszą wiedzą o swoim ciele.',
    contents: [
      'Protokoły powrotu po typowych kontuzjach (kolano, bark, kręgosłup)',
      'Ćwiczenia aktywacyjne i stabilizacyjne',
      'Progresja obciążeń bezpieczna dla tkanek',
      'Komunikacja z fizjoterapeutą (wytyczne)',
      'Plan przejścia z rehab do pełnego treningu',
    ],
    forWho: 'Dla zawodników po kontuzjach lub z przewlekłymi przeciążeniami. Program nie zastępuje wizyty u fizjoterapeuty — uzupełnia ją.',
    whyFor: 'Odpowiedni powrót po urazie jest kluczowy, by nie wpaść w pętlę nawracających kontuzji. Rehab TC uczy jak trenować z głową przez całe życie.',
  },
  {
    icon: '🏃',
    tag: '',
    title: 'Bieganie',
    lead: 'Od pierwszego kilometra do maratonu. Program biegowy oparty na strefach tętna i periodyzacji — bez zbędnego bólu i przetrenowania.',
    contents: [
      'Plany od 5 km, 10 km, półmaratonu i maratonu',
      'Trening w strefach tętna (easy, threshold, VO2max)',
      'Interwały, tempo runs, długie biegi',
      'Siła biegacza: ćwiczenia uzupełniające',
      'Strategia wyścigu i analiza tempa',
    ],
    forWho: 'Dla osób stawiających pierwsze kroki w bieganiu, jak i dla tych z bazą, którzy chcą przebić swoje rekordy życiowe.',
    whyFor: 'Bieganie jest jedną z najbardziej dostępnych form aktywności. Odpowiedni plan zamienia je z męki w przyjemność i daje mierzalne wyniki.',
  },
  {
    icon: '🖐️',
    tag: '',
    title: 'Trening Chwytu',
    lead: 'Siła dłoni i przedramion to ogniwo, które limituje Twoje wyniki we wszystkim — od podciągania po martwy ciąg. Przestań je ignorować.',
    contents: [
      'Trening siły uścisku (crush, pinch, support grip)',
      'Wytrzymałość chwytu na czas i powtórzenia',
      'Ćwiczenia na wałku i taśmach',
      'Protokoły pod wspinaczkę, CrossFit i trójbój',
      'Praca z grippers, hangerboard i ciężarkami palcowymi',
    ],
    forWho: 'Dla wspinaczy, zawodników CrossFit, trójboistów i każdego, komu wysuwa się drążek lub sztanga w kluczowych momentach.',
    whyFor: 'Silniejszy chwyt = więcej powtórzeń, większe ciężary, mniej wypadania ze sprzętu. To jeden z najbardziej niedocenianych elementów treningu siłowego.',
  },
];

const programModal = document.getElementById('programModal');
const modalClose = document.getElementById('programModalClose');

function openProgramModal(index) {
  const data = programData[index];
  if (!data) return;

  document.getElementById('modalIcon').textContent = data.icon;
  document.getElementById('modalTag').textContent = data.tag;
  document.getElementById('modalTitle').textContent = data.title;
  document.getElementById('modalLead').textContent = data.lead;
  document.getElementById('modalForWho').textContent = data.forWho;
  document.getElementById('modalWhyFor').textContent = data.whyFor;

  const list = document.getElementById('modalContents');
  list.innerHTML = data.contents.map(item => `<li>${item}</li>`).join('');

  programModal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeProgramModal() {
  if (!programModal?.classList.contains('open')) return;
  programModal.classList.remove('open');
  document.body.style.overflow = '';
}

document.querySelectorAll('.program-card').forEach((card, index) => {
  card.style.cursor = 'pointer';
  card.addEventListener('click', () => openProgramModal(index));
});

modalClose?.addEventListener('click', closeProgramModal);

programModal?.addEventListener('click', (e) => {
  if (e.target === programModal) closeProgramModal();
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeProgramModal();
});

document.querySelector('.program-modal-cta')?.addEventListener('click', closeProgramModal);

// ===== GALLERY + LIGHTBOX (szkolenia.html) =====
const gallery = document.getElementById('gallery');
const lightbox = document.getElementById('lightbox');
const galleryItems = typeof TC_GALLERY !== 'undefined' ? TC_GALLERY : [];
let lightboxIndex = 0;

if (gallery) {
  if (galleryItems.length) {
    gallery.innerHTML = galleryItems.map((item, index) => `
      <button class="gallery-item" data-index="${index}" aria-label="Powiększ zdjęcie: ${item.alt || ''}">
        <img src="${item.src}" alt="${item.alt || ''}" loading="lazy" />
        ${item.caption ? `<span class="gallery-caption">${item.caption}</span>` : ''}
      </button>
    `).join('');

    gallery.querySelectorAll('.gallery-item').forEach(button => {
      button.addEventListener('click', () => openLightbox(Number(button.dataset.index)));
    });
  } else {
    gallery.innerHTML = Array.from({ length: 6 }, () => `
      <div class="gallery-item gallery-placeholder"><span>Zdjęcie wkrótce</span></div>
    `).join('');
  }
}

function showLightboxImage(index) {
  lightboxIndex = (index + galleryItems.length) % galleryItems.length;
  const item = galleryItems[lightboxIndex];
  const img = document.getElementById('lightboxImg');
  img.src = item.src;
  img.alt = item.alt || '';
  document.getElementById('lightboxCaption').textContent = item.caption || '';
}

function openLightbox(index) {
  showLightboxImage(index);
  lightbox.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  if (!lightbox?.classList.contains('open')) return;
  lightbox.classList.remove('open');
  document.body.style.overflow = '';
}

document.getElementById('lightboxClose')?.addEventListener('click', closeLightbox);
document.getElementById('lightboxPrev')?.addEventListener('click', () => showLightboxImage(lightboxIndex - 1));
document.getElementById('lightboxNext')?.addEventListener('click', () => showLightboxImage(lightboxIndex + 1));

lightbox?.addEventListener('click', (e) => {
  if (e.target === lightbox) closeLightbox();
});

document.addEventListener('keydown', (e) => {
  if (!lightbox?.classList.contains('open')) return;
  if (e.key === 'Escape') closeLightbox();
  if (e.key === 'ArrowLeft') showLightboxImage(lightboxIndex - 1);
  if (e.key === 'ArrowRight') showLightboxImage(lightboxIndex + 1);
});

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
