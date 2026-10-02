from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class ShopTests(TestCase):
    def setUp(self):
        # Kategorie tworzy migracja 0002
        self.shoes = Category.objects.get(slug='obuwie')
        self.accessories = Category.objects.get(slug='akcesoria')
        self.shoe = Product.objects.create(
            category=self.shoes, name='TC Lifter', slug='tc-lifter', price=Decimal('499.00'),
            sale_price=Decimal('449.00'), sizes='40, 41, 42', buy_url='https://sklep.example.com/tc-lifter',
        )
        self.belt = Product.objects.create(category=self.accessories, name='Pas TC', slug='pas-tc', price=Decimal('149.00'))

    def test_list_shows_active_products(self):
        Product.objects.create(category=self.shoes, name='Ukryty', slug='ukryty', price=1, is_active=False)

        response = self.client.get(reverse('shop:list'))

        self.assertContains(response, 'TC Lifter')
        self.assertContains(response, 'Pas TC')
        self.assertNotContains(response, 'Ukryty')

    def test_category_filter(self):
        response = self.client.get(reverse('shop:list'), {'kategoria': 'akcesoria'})

        self.assertContains(response, 'Pas TC')
        self.assertNotContains(response, 'TC Lifter')

    def test_unknown_category_is_404(self):
        response = self.client.get(reverse('shop:list'), {'kategoria': 'nie-ma'})
        self.assertEqual(response.status_code, 404)

    def test_detail_links_to_shoper_and_shows_sizes(self):
        response = self.client.get(self.shoe.get_absolute_url())

        self.assertContains(response, 'href="https://sklep.example.com/tc-lifter"')
        self.assertContains(response, '449 zł')
        self.assertEqual(self.shoe.size_list, ['40', '41', '42'])

    def test_detail_without_buy_url_is_coming_soon(self):
        response = self.client.get(self.belt.get_absolute_url())
        self.assertContains(response, 'Dostępne wkrótce')
