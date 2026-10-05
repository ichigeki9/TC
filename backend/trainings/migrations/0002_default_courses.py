from django.db import migrations

# Szkolenia, które wcześniej były wpisane na sztywno w public/szkolenia.html
COURSES = [
    {
        'slug': 'trener-personalny', 'icon': '🏋️‍♂️', 'badge': 'Bestseller',
        'title': 'Trener Personalny — Kurs Certyfikowany',
        'meta': '12 tygodni · Online + Praktyki · Certyfikat uznawany w UE',
        'description': 'Kompletna ścieżka dla osób, które chcą zawodowo prowadzić treningi. Anatomia i fizjologia wysiłku, '
                       'technika ruchów bazowych, planowanie treningu i praca z klientem.',
        'points': 'Moduły online + zajęcia praktyczne na sali\nProgramowanie treningu dla różnych celów i poziomów\n'
                  'Egzamin końcowy i certyfikat',
    },
    {
        'slug': 'zywienie-sportowe', 'icon': '🥦', 'badge': 'Nowość',
        'title': 'Żywienie w Sporcie — Podstawy i Zaawansowane',
        'meta': '8 tygodni · 100% Online · Dostęp dożywotni',
        'description': 'Jak jeść pod trening siłowy, wytrzymałościowy i hybrydowy. Bilans energetyczny, makroskładniki, '
                       'nawodnienie, suplementacja i żywienie w dniu zawodów.',
        'points': 'Lekcje wideo w swoim tempie\nGotowe narzędzia i kalkulatory\nStudia przypadków zawodników',
    },
    {
        'slug': 'crossfit-l1', 'icon': '🎽', 'badge': 'Polecany',
        'title': 'CrossFit Level 1 — Przygotowanie do Egzaminu',
        'meta': '6 tygodni · Weekend + Online · 95% zdawalność',
        'description': 'Przygotowanie teoretyczne i praktyczne do egzaminu CrossFit Level 1. Dziewięć ruchów '
                       'fundamentalnych, metodyka nauczania i prowadzenia zajęć grupowych.',
        'points': 'Weekendowe zajęcia praktyczne\nPróbne testy egzaminacyjne\nKorekta techniki na wideo',
    },
    {
        'slug': 'metodyka-treningu', 'icon': '📐', 'badge': 'Popularny',
        'title': 'Metodyka Treningu Funkcjonalnego',
        'meta': '4 tygodnie · Online · Idealne dla trenerów siłowni',
        'description': 'Jak budować skuteczne jednostki i mikrocykle treningu funkcjonalnego. Dobór ćwiczeń, skalowanie, '
                       'progresja i prowadzenie grup o różnym poziomie.',
        'points': 'Gotowe szablony planowania\nSkalowanie ćwiczeń dla każdego poziomu\nAnaliza realnych programów TC',
    },
    {
        'slug': 'psychologia-sportu', 'icon': '🧠', 'badge': '',
        'title': 'Psychologia Sportu — Mentalna Siła Zawodnika',
        'meta': '5 tygodni · Online + Live sesje · Grupowe mentorstwo',
        'description': 'Motywacja, koncentracja, radzenie sobie ze stresem startowym i budowanie nawyków. Narzędzia, '
                       'które pomagają wygrywać w głowie, zanim wygrasz na zawodach.',
        'points': 'Sesje live z prowadzącym\nĆwiczenia mentalne do codziennego treningu\nGrupowe mentorstwo',
    },
]


def create_courses(apps, schema_editor):
    Training = apps.get_model('trainings', 'Training')
    if Training.objects.exists():
        return
    for order, course in enumerate(COURSES):
        Training.objects.create(kind='course', order=order, **course)


class Migration(migrations.Migration):
    dependencies = [('trainings', '0001_initial')]

    operations = [migrations.RunPython(create_courses, migrations.RunPython.noop)]
