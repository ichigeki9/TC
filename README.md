# Training Culture

- `public/` — statyczna strona główna (index.html, css, js, images).
  Adres planów treningowych: `public/js/config.js`.
- `backend/` — Django: sklep z koszykiem i zamówieniami (`/sklep/`), szkolenia i campy (`/szkolenia/`),
  konta (logowanie e-mailem, `/konto/`), ranking wyników (`/ranking/`) i panel admina (`/admin/`).
  Django serwuje też całą stronę z `public/` (WhiteNoise), więc wszystko działa pod jedną domeną.

## Uruchomienie lokalnie

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env    # potem w .env ustaw DJANGO_DEBUG=1 i wpisz dane poczty
cd backend
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py createsuperuser   # konto do panelu /admin/
../.venv/bin/python manage.py seed_demo         # przykładowe produkty ze zdjęciami (opcjonalnie)
../.venv/bin/python manage.py runserver
```

Strona: http://localhost:8000 · Ranking: http://localhost:8000/ranking/ · Panel: http://localhost:8000/admin/

Testy: `../.venv/bin/python manage.py test`

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
Galeria zdjęć na dole strony: wrzuć pliki (.jpg, .jpeg, .png, .webp) do `public/images/szkolenia/` — kolejność według nazwy pliku.
Zdjęcia kart „Znajdź swój program”: `public/images/programy/<program>.jpeg` (np. `crossfit.jpeg`, `trening-silowy.jpeg`).
Zdjęcie dużego kafelka „Campy Training Culture” na /szkolenia/: dowolny plik w `public/images/campy/`.

## Maile (Brevo)

Strona wysyła maile: link aktywacyjny po rejestracji (konto działa dopiero po kliknięciu), reset hasła,
potwierdzenie przyjęcia zamówienia, potwierdzenie płatności i informację o wysyłce
(akcja „Oznacz jako wysłane” albo zmiana statusu w formularzu zamówienia). Na `SHOP_NOTIFY_EMAIL`
przychodzi powiadomienie o każdym opłaconym zamówieniu. Treści maili: `backend/templates/emails/`.

Maile idą przez SMTP Brevo (darmowo 300 dziennie). W Brevo: **Senders** → dodaj i potwierdź adres nadawcy,
potem **SMTP & API → SMTP** → skopiuj login i wygeneruj klucz SMTP. Zmienne `EMAIL_*`, `DEFAULT_FROM_EMAIL`
i `SHOP_NOTIFY_EMAIL` jak w `.env.example` — lokalnie wpisz je do pliku `.env`.
Test wysyłki: `python manage.py sendtestemail adres@example.com` (w katalogu `backend`).
Lokalnie bez `EMAIL_HOST` maile tylko wypisują się w terminalu z `runserver`.

## Wdrożenie na Northflank

1. Projekt → **Add-on** → PostgreSQL.
2. **Combined service** z repozytorium Git, build: **Dockerfile** (katalog główny repo), port **8080** HTTP, publiczny.
3. Zmienne środowiskowe jak w `.env.example`:
   - `DJANGO_SECRET_KEY` — długi losowy ciąg (np. `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`),
   - `DJANGO_ALLOWED_HOSTS` i `DJANGO_CSRF_TRUSTED_ORIGINS` — domena serwisu (`…code.run`) i docelowa domena,
   - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (jako sekret),
     `DEFAULT_FROM_EMAIL`, `SHOP_NOTIFY_EMAIL` — poczta Brevo,
   - `DATABASE_URL` — adres połączenia z addonu Postgres (Northflank: połącz sekrety addonu z serwisem
     i przypisz jego connection URI do `DATABASE_URL`).
4. **Volume** (trwały dysk) podpięty do serwisu, zamontowany w `/app/media`, oraz zmienna
   `DJANGO_MEDIA_ROOT=/app/media`. Tam trafiają zdjęcia wgrywane w panelu — bez wolumenu znikają przy każdym wdrożeniu.
5. Migracje uruchamiają się same przy starcie. Konto admina: w Northflanku otwórz **Shell** kontenera i uruchom
   `python manage.py createsuperuser`.
   Przykładowe produkty ze zdjęciami: `python manage.py seed_demo`.
