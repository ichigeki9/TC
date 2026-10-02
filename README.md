# Training Culture

- `public/` — statyczna strona (index.html, szkolenia.html, css, js, images).
  Adres planów treningowych oraz galeria szkoleń: `public/js/config.js`.
- `backend/` — Django: katalog sklepu (`/sklep/`), konta (logowanie e-mailem), ranking wyników (`/ranking/`, `/konto/`)
  i panel admina (`/admin/`).
  Django serwuje też całą stronę z `public/` (WhiteNoise), więc wszystko działa pod jedną domeną.

## Uruchomienie lokalnie

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd backend
export DJANGO_DEBUG=1
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py createsuperuser   # konto do panelu /admin/
../.venv/bin/python manage.py runserver
```

Strona: http://localhost:8000 · Ranking: http://localhost:8000/ranking/ · Panel: http://localhost:8000/admin/

Testy: `DJANGO_DEBUG=1 ../.venv/bin/python manage.py test`

## Dodawanie treningów do rankingu

Panel `/admin/` → **Treningi** → Dodaj. Typ wyniku decyduje o sortowaniu:
czas (mniej = lepiej), powtórzenia lub kg (więcej = lepiej).
W panelu można też usuwać wyniki (**Wyniki**) i blokować konta (**Użytkownicy** → odznacz „aktywny”).

## Sklep (katalog)

Panel `/admin/` → **Produkty** → Dodaj: nazwa, kategoria (Obuwie / Odzież / Akcesoria), cena, opcjonalnie cena
promocyjna, rozmiary, etykieta i opis. **Zdjęcie**: adres obrazka (np. skopiowany z produktu w Shoperze) albo plik
wrzucony do `public/images/sklep/` wpisany jako `/images/sklep/nazwa.jpg`. **Link do zakupu**: adres produktu
w Shoperze. Bez niego przycisk pokazuje „Dostępne wkrótce”.
Koszyk, płatności i wysyłka są w Shoperze; u nas jest tylko katalog.

## Wdrożenie na Northflank

1. Projekt → **Add-on** → PostgreSQL.
2. **Combined service** z repozytorium Git, build: **Dockerfile** (katalog główny repo), port **8080** HTTP, publiczny.
3. Zmienne środowiskowe jak w `.env.example`:
   - `DJANGO_SECRET_KEY` — długi losowy ciąg (np. `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`),
   - `DJANGO_ALLOWED_HOSTS` i `DJANGO_CSRF_TRUSTED_ORIGINS` — domena serwisu (`…code.run`) i docelowa domena,
   - `DATABASE_URL` — adres połączenia z addonu Postgres (Northflank: połącz sekrety addonu z serwisem
     i przypisz jego connection URI do `DATABASE_URL`).
4. Migracje uruchamiają się same przy starcie. Konto admina: w Northflanku otwórz **Shell** kontenera i uruchom
   `python manage.py createsuperuser`.
