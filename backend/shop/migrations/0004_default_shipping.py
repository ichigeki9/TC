from decimal import Decimal

from django.db import migrations

# Robocze stawki — do zmiany w panelu (Sklep → Sposoby dostawy)
METHODS = [('Kurier', Decimal('19.99')), ('Paczkomat InPost', Decimal('14.99'))]


def create_methods(apps, schema_editor):
    ShippingMethod = apps.get_model('shop', 'ShippingMethod')
    if ShippingMethod.objects.exists():
        return
    for order, (name, price) in enumerate(METHODS):
        ShippingMethod.objects.create(name=name, price=price, order=order)


class Migration(migrations.Migration):
    dependencies = [('shop', '0003_orders')]

    operations = [migrations.RunPython(create_methods, migrations.RunPython.noop)]
