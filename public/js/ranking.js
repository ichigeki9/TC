// Ranking: doczytywanie starszych tygodni i dni tygodnia dopiero na żądanie
(function () {
  async function fetchHtml(url) {
    const response = await fetch(url, { headers: { 'X-Requested-With': 'fetch' } });
    if (!response.ok) throw new Error(response.status);
    return response.text();
  }

  // „Pokaż wcześniejsze tygodnie” — wstawia nagłówki tygodni i nowy przycisk na miejsce starego
  document.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-load-more]');
    if (!button || button.disabled) return;
    button.disabled = true;
    button.textContent = 'Ładowanie…';
    try {
      button.insertAdjacentHTML('beforebegin', await fetchHtml(button.dataset.loadMore));
      button.remove();
    } catch {
      button.disabled = false;
      button.textContent = 'Nie udało się — spróbuj ponownie';
    }
  });

  // Rozwinięcie tygodnia — za pierwszym razem pobiera jego dni
  document.addEventListener('toggle', async (event) => {
    const details = event.target;
    if (!details.matches('details[data-src]') || !details.open || details.dataset.loaded) return;
    details.dataset.loaded = '1';
    const body = details.querySelector('[data-lazy-body]');
    try {
      body.innerHTML = await fetchHtml(details.dataset.src);
    } catch {
      delete details.dataset.loaded;
      body.innerHTML = '<p class="tc-muted">Nie udało się wczytać. Zwiń i rozwiń ponownie.</p>';
    }
  }, true);
})();
