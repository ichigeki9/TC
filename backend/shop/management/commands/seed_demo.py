from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from shop.models import Category, Product

# Zdjęcia z Unsplash (licencja pozwala na użycie komercyjne), przycięte do kwadratu:
#   tc-lifter               unsplash.com/photos/dP-h8Cm4UXA
#   tc-runner-hybrid        unsplash.com/photos/bE6k8SQT2FQ
#   koszulka-tc-performance unsplash.com/photos/DjCo6_Rr4nE
#   bluza-tc-heavy          unsplash.com/photos/REOoETloFqE
#   pas-tc-lever            unsplash.com/photos/eJCPaYMZLLA
#   owijki-na-nadgarstki    unsplash.com/photos/hOuJYX2K5DA
IMAGES_DIR = Path(__file__).resolve().parent.parent.parent / 'seed_images'
PLACEHOLDER_DESCRIPTION = 'Przykładowy opis produktu.'

PRODUCTS = [
    {
        'slug': 'tc-lifter', 'category': 'obuwie', 'name': 'TC Lifter', 'price': '499.00', 'sale_price': '449.00',
        'sizes': '39, 40, 41, 42, 43, 44, 45', 'badge': 'Bestseller',
        'description': 'Buty do podnoszenia ciężarów ze stabilną, płaską podeszwą i wzmocnioną piętą.\n'
                       'Pewne oparcie w przysiadzie, martwym ciągu i dwuboju.',
    },
    {
        'slug': 'tc-runner-hybrid', 'category': 'obuwie', 'name': 'TC Runner Hybrid', 'price': '429.00',
        'sizes': '38, 39, 40, 41, 42, 43, 44, 45', 'badge': 'Nowość',
        'description': 'Lekkie buty do treningu hybrydowego: bieganie, sanki, wykroki i ergometr w jednej parze.\n'
                       'Przewiewna cholewka i amortyzacja, która nie odbiera stabilności.',
    },
    {
        'slug': 'koszulka-tc-performance', 'category': 'odziez', 'name': 'Koszulka TC Performance', 'price': '119.00',
        'sizes': 'S, M, L, XL, XXL', 'badge': '',
        'description': 'Oddychająca koszulka treningowa o luźnym kroju.\n'
                       'Szybko schnie i nie krępuje ruchów nad głową.',
    },
    {
        'slug': 'bluza-tc-heavy', 'category': 'odziez', 'name': 'Bluza TC Heavy', 'price': '249.00',
        'sizes': 'S, M, L, XL, XXL', 'badge': '',
        'description': 'Gruba bluza z kapturem z ciężkiej bawełny.\n'
                       'Na rozgrzewkę, między seriami i po treningu.',
    },
    {
        'slug': 'pas-tc-lever', 'category': 'akcesoria', 'name': 'Pas TC Lever', 'price': '299.00',
        'sizes': 'S, M, L, XL', 'badge': '',
        'description': 'Skórzany pas do treningu siłowego o szerokości 10 cm.\n'
                       'Sztywne podparcie tułowia przy ciężkich przysiadach i martwych ciągach.',
    },
    {
        'slug': 'owijki-na-nadgarstki', 'category': 'akcesoria', 'name': 'Owijki na nadgarstki', 'price': '79.00',
        'sizes': '', 'badge': '',
        'description': 'Elastyczne owijki stabilizujące nadgarstki przy wyciskaniu, podrzucie i ćwiczeniach gimnastycznych.\n'
                       'Sprzedawane w parze, zapięcie na rzep.',
    },
]


class Command(BaseCommand):
    help = 'Dodaje przykładowe produkty sklepu ze zdjęciami. Można uruchamiać wielokrotnie — niczego nie nadpisuje.'

    def handle(self, *args, **options):
        categories = {category.slug: category for category in Category.objects.all()}

        for order, data in enumerate(PRODUCTS):
            data = dict(data)
            slug = data.pop('slug')
            data['category'] = categories[data['category']]
            data['price'] = Decimal(data['price'])
            if 'sale_price' in data:
                data['sale_price'] = Decimal(data['sale_price'])

            # Produkt rozpoznajemy po adresie albo po nazwie (starsze wpisy miały inne adresy)
            product = Product.objects.filter(slug=slug).first() or Product.objects.filter(name=data['name']).first()
            created = product is None
            if created:
                product = Product.objects.create(slug=slug, order=order, **data)

            # Istniejącym produktom uzupełniamy tylko puste pola — zmian z panelu nie ruszamy
            changed = []
            if not created:
                for field in ('description', 'sizes'):
                    if getattr(product, field) in ('', PLACEHOLDER_DESCRIPTION) and data[field]:
                        setattr(product, field, data[field])
                        changed.append(field)
                if changed:
                    product.save(update_fields=changed)

            if not product.image:
                with open(IMAGES_DIR / f'{slug}.jpg', 'rb') as image:
                    product.image.save(f'{slug}.jpg', File(image), save=True)
                changed.append('image')

            status = 'dodano' if created else (f'uzupełniono: {", ".join(changed)}' if changed else 'bez zmian')
            self.stdout.write(f'{product.name}: {status}')
