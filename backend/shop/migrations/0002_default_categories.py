from django.db import migrations

CATEGORIES = [('Obuwie', 'obuwie'), ('Odzież', 'odziez'), ('Akcesoria', 'akcesoria')]


def create_categories(apps, schema_editor):
    Category = apps.get_model('shop', 'Category')
    for order, (name, slug) in enumerate(CATEGORIES):
        Category.objects.get_or_create(slug=slug, defaults={'name': name, 'order': order})


class Migration(migrations.Migration):
    dependencies = [('shop', '0001_initial')]

    operations = [migrations.RunPython(create_categories, migrations.RunPython.noop)]
