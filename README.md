# Training Culture

- `public/` — statyczna strona główna (index.html, css, js, images).
  Adres planów treningowych oraz galeria szkoleń: `public/js/config.js`.
- `backend/` — Django: sklep z koszykiem i zamówieniami (`/sklep/`), szkolenia i campy (`/szkolenia/`),
  konta (logowanie e-mailem, `/konto/`), ranking wyników (`/ranking/`) i panel admina (`/admin/`).
  Django serwuje też całą stronę z `public/` (WhiteNoise), więc wszystko działa pod jedną domeną.

## Uruchomienie lokalnie

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd backend
export DJANGO_DEBUG=1
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py createsuperuser   # konto do panelu /admin/
../.venv/bin/python manage.py seed_demo         # przykładowe produkty ze zdjęciami (opcjonalnie)
../.venv/bin/python manage.py runserver
```

Strona: http://localhost:8000 · Ranking: http://localhost:8000/ranking/ · Panel: http://localhost:8000/admin/

Testy: `DJANGO_DEBUG=1 ../.venv/bin/python manage.py test`

## Dodawanie treningów do rankingu

Panel `/admin/` → **Treningi** → Dodaj. Typ wyniku decyduje o sortowaniu:
czas (mniej = lepiej), powtórzenia lub kg (więcej = lepiej).
Pod formularzem treningu jest tabela **Ćwiczenia** — każdy wiersz to jedno ćwiczenie (nazwa + „ile / jak”,
np. „Wall balls — 50 powtórzeń”). Lista pokazuje się na stronie rankingu tego treningu.
W panelu można też usuwać wyniki (**Wyniki**) i blokować konta (**Użytkownicy** → odznacz „aktywny”).

## Sklep

Panel `/admin/` → **Produkty** → Dodaj: nazwa, kategoria (Obuwie / Odzież / Akcesoria), cena, opcjonalnie cena
promocyjna, zdjęcie (plik z dysku), rozmiary, etykieta i opis.

**Podgląd przed publikacją:** odznacz „widoczny”, zapisz i kliknij **Pokaż na stronie** (prawy górny róg formularza).
Ukryty produkt widzi tylko zalogowana obsługa. Gdy wygląda dobrze — zaznacz „widoczny”.

Klient może kupić bez konta (jako gość) albo zalogowany — wtedy zamówienie widzi w swoim profilu.
Zamówienia są w panelu w **Zamówienia** (filtr po statusie, akcja „Oznacz jako wysłane”),
ceny dostawy w **Sposoby dostawy**.

**Płatności są na razie testowe** — po złożeniu zamówienia klient trafia na ekran „Płatność testowa”
i sam wybiera, czy płatność się udała. Żadne pieniądze nie są pobierane, więc przed startem sprzedaży trzeba
podpiąć prawdziwą bramkę: nowa klasa w `backend/shop/payments.py` + zmienna `PAYMENT_PROVIDER`.

## Szkolenia i campy

Panel `/admin/` → **Szkolenia i campy** → Dodaj. Rodzaj (szkolenie / camp) decyduje, w której sekcji strony
`/szkolenia/` pojawi się wpis; lista na stronie głównej pobiera się sama. Podgląd ukrytych wpisów działa jak w sklepie.
Galeria zdjęć na dole strony: `public/js/config.js` (`TC_GALLERY`).

## Wdrożenie na Northflank

1. Projekt → **Add-on** → PostgreSQL.
2. **Combined service** z repozytorium Git, build: **Dockerfile** (katalog główny repo), port **8080** HTTP, publiczny.
3. Zmienne środowiskowe jak w `.env.example`:
   - `DJANGO_SECRET_KEY` — długi losowy ciąg (np. `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`),
   - `DJANGO_ALLOWED_HOSTS` i `DJANGO_CSRF_TRUSTED_ORIGINS` — domena serwisu (`…code.run`) i docelowa domena,
   - `DATABASE_URL` — adres połączenia z addonu Postgres (Northflank: połącz sekrety addonu z serwisem
     i przypisz jego connection URI do `DATABASE_URL`).
4. **Volume** (trwały dysk) podpięty do serwisu, zamontowany w `/app/media`, oraz zmienna
   `DJANGO_MEDIA_ROOT=/app/media`. Tam trafiają zdjęcia wgrywane w panelu — bez wolumenu znikają przy każdym wdrożeniu.
5. Migracje uruchamiają się same przy starcie. Konto admina: w Northflanku otwórz **Shell** kontenera i uruchom
   `python manage.py createsuperuser`.
   Przykładowe produkty ze zdjęciami: `python manage.py seed_demo`.
