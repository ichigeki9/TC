from decimal import Decimal
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from accounts.tests import activation_link

from .models import Category, Order, Product, ShippingMethod
from .payments import PROVIDERS

ADDRESS = {
    'full_name': 'Anna Nowak', 'email': 'anna@example.com', 'phone': '600 100 200',
    'street': 'Sportowa 1/2', 'postal_code': '19-300', 'city': 'Ełk', 'note': '',
}


class ShopTestCase(TestCase):
    def setUp(self):
        # Kategorie tworzy migracja 0002, sposoby dostawy migracja 0004
        self.shoes = Category.objects.get(slug='obuwie')
        self.accessories = Category.objects.get(slug='akcesoria')
        self.shoe = Product.objects.create(
            category=self.shoes, name='TC Lifter', slug='tc-lifter', price=Decimal('499.00'),
            sale_price=Decimal('449.00'), sizes='40, 41, 42',
        )
        self.belt = Product.objects.create(category=self.accessories, name='Pas TC', slug='pas-tc', price=Decimal('149.00'))
        self.courier = ShippingMethod.objects.get(name='Kurier')
        self.anna = User.objects.create_user('anna@example.com', 'haslo-testowe-123', display_name='Anna', gender='F')
        self.bartek = User.objects.create_user('bartek@example.com', 'haslo-testowe-123', display_name='Bartek', gender='M')

    def add_to_cart(self, product, **data):
        return self.client.post(reverse('shop:cart_add', args=[product.slug]), data)

    def place_order(self, **overrides):
        return self.client.post(reverse('shop:checkout'), {**ADDRESS, 'shipping': self.courier.pk, **overrides})


class CatalogTests(ShopTestCase):
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

    def test_detail_shows_sale_price_and_sizes(self):
        response = self.client.get(self.shoe.get_absolute_url())

        self.assertContains(response, '449 zł')
        self.assertContains(response, 'Dodaj do koszyka')
        self.assertEqual(self.shoe.size_list, ['40', '41', '42'])

    def test_hidden_product_is_visible_only_to_staff(self):
        hidden = Product.objects.create(category=self.shoes, name='Ukryty', slug='ukryty', price=1, is_active=False)
        self.assertEqual(self.client.get(hidden.get_absolute_url()).status_code, 404)

        admin = User.objects.create_superuser('admin@example.com', 'haslo-testowe-123')
        self.client.force_login(admin)
        response = self.client.get(hidden.get_absolute_url())

        self.assertContains(response, 'Podgląd')
        self.assertNotContains(response, 'Dodaj do koszyka')


class CartTests(ShopTestCase):
    def test_add_requires_size_when_product_has_sizes(self):
        self.add_to_cart(self.shoe)
        self.assertEqual(self.client.session.get('cart', {}), {})

        self.add_to_cart(self.shoe, size='99')
        self.assertEqual(self.client.session.get('cart', {}), {})

    def test_same_product_and_size_adds_up(self):
        self.add_to_cart(self.shoe, size='41', quantity=2)
        self.add_to_cart(self.shoe, size='41')
        self.add_to_cart(self.shoe, size='42')

        self.assertEqual(self.client.session['cart'], {f'{self.shoe.pk}:41': 3, f'{self.shoe.pk}:42': 1})

    def test_cart_page_uses_sale_price(self):
        self.add_to_cart(self.shoe, size='41', quantity=2)
        self.add_to_cart(self.belt)

        response = self.client.get(reverse('shop:cart'))

        self.assertEqual(response.context['total'], Decimal('1047.00'))

    def test_update_and_remove(self):
        self.add_to_cart(self.belt)
        key = f'{self.belt.pk}:'

        self.client.post(reverse('shop:cart_update'), {'key': key, 'quantity': 5})
        self.assertEqual(self.client.session['cart'], {key: 5})

        self.client.post(reverse('shop:cart_update'), {'key': key, 'quantity': 0})
        self.assertEqual(self.client.session['cart'], {})

    def test_hidden_product_drops_out_of_cart(self):
        self.add_to_cart(self.belt)
        self.belt.is_active = False
        self.belt.save()

        response = self.client.get(reverse('shop:cart'))

        self.assertEqual(response.context['lines'], [])


class CheckoutTests(ShopTestCase):
    def test_guest_can_order_without_account(self):
        self.add_to_cart(self.belt)
        self.assertContains(self.client.get(reverse('shop:checkout')), 'Kupujesz jako gość')

        response = self.place_order()

        order = Order.objects.get()
        self.assertRedirects(response, reverse('shop:payment_dummy', args=[order.token]))
        self.assertIsNone(order.user)
        self.assertEqual(order.total, Decimal('149.00') + self.courier.price)

        self.client.post(reverse('shop:payment_dummy', args=[order.token]), {'action': 'pay'})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertContains(self.client.get(order.get_absolute_url()), order.number)

    def test_guest_order_is_hidden_from_other_browsers_and_users(self):
        self.add_to_cart(self.belt)
        self.place_order()
        order = Order.objects.get()
        payment_url = reverse('shop:payment_dummy', args=[order.token])

        stranger = self.client_class()
        self.assertEqual(stranger.get(order.get_absolute_url()).status_code, 404)
        self.assertEqual(stranger.post(payment_url, {'action': 'pay'}).status_code, 404)

        stranger.force_login(self.bartek)
        self.assertEqual(stranger.get(order.get_absolute_url()).status_code, 404)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.NEW)

    def test_registration_returns_to_checkout_after_activation(self):
        self.add_to_cart(self.belt)

        self.client.post(f"{reverse('accounts:register')}?next={reverse('shop:checkout')}", {
            'email': 'nowy@example.com', 'display_name': 'Nowy', 'gender': 'M',
            'password1': 'haslo-testowe-123', 'password2': 'haslo-testowe-123',
        })
        response = self.client.get(activation_link(mail.outbox[0]))

        self.assertRedirects(response, reverse('shop:checkout'))
        # Koszyk przeżywa logowanie
        self.assertEqual(len(self.client.session['cart']), 1)

    def test_registration_ignores_foreign_next(self):
        self.client.post(f"{reverse('accounts:register')}?next=https://zly.example.com/", {
            'email': 'nowy@example.com', 'display_name': 'Nowy', 'gender': 'M',
            'password1': 'haslo-testowe-123', 'password2': 'haslo-testowe-123',
        })

        self.assertNotIn('zly.example.com', mail.outbox[0].body)
        self.assertRedirects(self.client.get(activation_link(mail.outbox[0])), reverse('ranking:list'))

    def test_empty_cart_goes_back_to_cart(self):
        self.client.force_login(self.anna)
        self.assertRedirects(self.client.get(reverse('shop:checkout')), reverse('shop:cart'))

    def test_order_is_created_with_prices_from_database(self):
        self.client.force_login(self.anna)
        self.add_to_cart(self.shoe, size='41', quantity=2)
        self.add_to_cart(self.belt)

        response = self.place_order()

        order = Order.objects.get()
        self.assertRedirects(response, reverse('shop:payment_dummy', args=[order.token]))
        self.assertEqual(order.user, self.anna)
        self.assertEqual(order.status, Order.Status.NEW)
        self.assertEqual(order.total, Decimal('1047.00') + self.courier.price)
        self.assertEqual(order.shipping_name, 'Kurier')
        self.assertEqual(
            sorted(order.items.values_list('name', 'size', 'unit_price', 'quantity')),
            [('Pas TC', '', Decimal('149.00'), 1), ('TC Lifter', '41', Decimal('449.00'), 2)],
        )
        self.assertEqual(self.client.session.get('cart', {}), {})

    def test_invalid_address_does_not_create_order(self):
        self.client.force_login(self.anna)
        self.add_to_cart(self.belt)

        response = self.place_order(postal_code='19300')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Podaj kod w formacie 00-000.')
        self.assertFalse(Order.objects.exists())

    def test_later_price_change_does_not_change_order(self):
        self.client.force_login(self.anna)
        self.add_to_cart(self.belt)
        self.place_order()

        self.belt.price = Decimal('999.00')
        self.belt.save()

        order = Order.objects.get()
        self.assertEqual(order.items.get().unit_price, Decimal('149.00'))
        self.assertEqual(order.items_total, Decimal('149.00'))


class PaymentTests(ShopTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.anna)
        self.add_to_cart(self.belt)
        self.place_order()
        self.order = Order.objects.get()
        self.payment_url = reverse('shop:payment_dummy', args=[self.order.token])

    def test_pay_marks_order_paid(self):
        response = self.client.post(self.payment_url, {'action': 'pay'})

        self.order.refresh_from_db()
        self.assertRedirects(response, self.order.get_absolute_url())
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertIsNotNone(self.order.paid_at)

    def test_cancel_marks_order_cancelled(self):
        self.client.post(self.payment_url, {'action': 'cancel'})

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertIsNone(self.order.paid_at)

    def test_paid_order_cannot_be_paid_or_cancelled_again(self):
        self.client.post(self.payment_url, {'action': 'pay'})
        self.client.post(self.payment_url, {'action': 'cancel'})

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)

    def test_other_user_cannot_see_or_pay_order(self):
        anonymous = self.client_class()
        other_user = self.client_class()
        other_user.force_login(self.bartek)

        for stranger in (anonymous, other_user):
            self.assertEqual(stranger.get(self.order.get_absolute_url()).status_code, 404)
            self.assertEqual(stranger.post(self.payment_url, {'action': 'pay'}).status_code, 404)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.NEW)

    def test_dummy_screen_disappears_with_real_provider(self):
        class RealProvider:
            name = 'real'

        with mock.patch.dict(PROVIDERS, {'real': RealProvider}), self.settings(PAYMENT_PROVIDER='real'):
            response = self.client.post(self.payment_url, {'action': 'pay'})

        self.assertEqual(response.status_code, 404)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.NEW)

    def test_order_is_listed_on_profile(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertContains(response, self.order.number)


# Bez powiadomień dla sklepu, chyba że test włącza je sam — inaczej liczby maili zależą od .env
@override_settings(SHOP_NOTIFY_EMAIL='')
class OrderEmailTests(ShopTestCase):
    def test_guest_gets_order_and_payment_emails_without_link(self):
        self.add_to_cart(self.belt)
        self.place_order()
        order = Order.objects.get()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['anna@example.com'])
        self.assertIn(order.number, mail.outbox[0].subject)
        self.assertIn('1 × Pas TC', mail.outbox[0].body)
        self.assertNotIn('http', mail.outbox[0].body)

        self.client.post(reverse('shop:payment_dummy', args=[order.token]), {'action': 'pay'})
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('Płatność', mail.outbox[1].subject)

    def test_customer_with_account_gets_order_link(self):
        self.client.force_login(self.anna)
        self.add_to_cart(self.belt)
        self.place_order()
        order = Order.objects.get()

        self.assertIn(f'http://testserver{order.get_absolute_url()}', mail.outbox[0].body)

    def test_cancelled_payment_sends_no_email(self):
        self.add_to_cart(self.belt)
        self.place_order()
        order = Order.objects.get()

        self.client.post(reverse('shop:payment_dummy', args=[order.token]), {'action': 'cancel'})
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(SHOP_NOTIFY_EMAIL='sklep@example.com')
    def test_shop_is_notified_about_paid_order(self):
        self.add_to_cart(self.belt)
        self.place_order()
        order = Order.objects.get()
        self.client.post(reverse('shop:payment_dummy', args=[order.token]), {'action': 'pay'})

        notify = mail.outbox[-1]
        self.assertEqual(notify.to, ['sklep@example.com'])
        self.assertIn(reverse('admin:shop_order_change', args=[order.pk]), notify.body)

    def test_admin_ship_action_emails_only_paid_orders(self):
        self.add_to_cart(self.belt)
        self.place_order()
        paid = Order.objects.get()
        paid.mark_paid('TEST')
        self.add_to_cart(self.belt)
        self.place_order(email='inny@example.com')
        mail.outbox.clear()

        admin = User.objects.create_superuser('admin@example.com', 'haslo-testowe-123')
        self.client.force_login(admin)
        self.client.post(reverse('admin:shop_order_changelist'), {
            'action': 'mark_shipped', '_selected_action': [o.pk for o in Order.objects.all()],
        })

        paid.refresh_from_db()
        self.assertEqual(paid.status, Order.Status.SHIPPED)
        self.assertEqual([m.to for m in mail.outbox], [['anna@example.com']])
        self.assertIn('wysłane', mail.outbox[0].subject)
