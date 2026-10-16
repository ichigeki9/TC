from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import Cart
from .emails import send_order_email
from .forms import CheckoutForm
from .models import Category, Order, OrderItem, Product
from .payments import get_provider

ADDRESS_FIELDS = ('full_name', 'email', 'phone', 'street', 'postal_code', 'city')
# Zamówienia złożone bez konta — gość widzi je tylko w tej samej przeglądarce
GUEST_ORDERS_KEY = 'guest_orders'


def product_list(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).select_related('category')

    current = None
    slug = request.GET.get('kategoria')
    if slug:
        current = get_object_or_404(Category, slug=slug)
        products = products.filter(category=current)

    return render(request, 'shop/list.html', {
        'categories': categories,
        'current': current,
        'products': products,
    })


def product_detail(request, slug):
    # Obsługa sklepu widzi też ukryte produkty — to podgląd przed publikacją
    products = Product.objects.select_related('category')
    if not request.user.is_staff:
        products = products.filter(is_active=True)
    product = get_object_or_404(products, slug=slug)
    related = Product.objects.filter(is_active=True, category=product.category).exclude(pk=product.pk)[:4]
    return render(request, 'shop/detail.html', {'product': product, 'related': related})


def parse_quantity(raw, default=1):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def cart_detail(request):
    lines = Cart(request).lines()
    return render(request, 'shop/cart.html', {'lines': lines, 'total': Cart.total(lines)})


@require_POST
def cart_add(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    size = request.POST.get('size', '')
    if product.size_list and size not in product.size_list:
        messages.error(request, 'Wybierz rozmiar.')
        return redirect(product)
    if not product.size_list:
        size = ''

    quantity = max(parse_quantity(request.POST.get('quantity')), 1)
    Cart(request).add(product, size, quantity)
    messages.success(request, f'Dodano do koszyka: {product.name}')
    return redirect('shop:cart')


@require_POST
def cart_update(request):
    quantity = parse_quantity(request.POST.get('quantity'), default=0)
    Cart(request).set_quantity(request.POST.get('key', ''), quantity)
    return redirect('shop:cart')


def checkout(request):
    cart = Cart(request)
    lines = cart.lines()
    if not lines:
        messages.error(request, 'Twój koszyk jest pusty.')
        return redirect('shop:cart')

    # Zalogowanym podpowiadamy dane z poprzedniego zamówienia
    initial = {}
    if request.user.is_authenticated:
        initial = {'email': request.user.email}
        last_order = Order.objects.filter(user=request.user).first()
        if last_order:
            initial = {field: getattr(last_order, field) for field in ADDRESS_FIELDS}

    form = CheckoutForm(request.POST or None, initial=initial)
    items_total = Cart.total(lines)

    if request.method == 'POST' and form.is_valid():
        shipping = form.cleaned_data['shipping']
        provider = get_provider()
        with transaction.atomic():
            order = form.save(commit=False)
            order.user = request.user if request.user.is_authenticated else None
            order.shipping_name = shipping.name
            order.shipping_price = shipping.price
            order.total = items_total + shipping.price
            order.payment_provider = provider.name
            order.save()
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order, product=line['product'], name=line['product'].name, size=line['size'],
                    unit_price=line['unit_price'], quantity=line['quantity'],
                )
                for line in lines
            ])
        cart.clear()
        send_order_email(request, order, 'placed')
        if order.user is None:
            request.session[GUEST_ORDERS_KEY] = [*request.session.get(GUEST_ORDERS_KEY, []), str(order.token)]
        return redirect(provider.start(order))

    return render(request, 'shop/checkout.html', {'form': form, 'lines': lines, 'items_total': items_total})


def get_own_order(request, token):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), token=token)
    if request.user.is_staff:
        return order
    if order.user_id:
        allowed = order.user_id == request.user.id
    else:
        allowed = str(order.token) in request.session.get(GUEST_ORDERS_KEY, [])
    if not allowed:
        raise Http404
    return order


def order_detail(request, token):
    order = get_own_order(request, token)
    payment_url = get_provider().start(order) if order.is_awaiting_payment else None
    return render(request, 'shop/order_detail.html', {'order': order, 'payment_url': payment_url})


def payment_dummy(request, token):
    """Ekran udający bramkę płatności. Znika, gdy PAYMENT_PROVIDER wskaże prawdziwą bramkę."""
    if get_provider().name != 'dummy':
        raise Http404
    order = get_own_order(request, token)
    if not order.is_awaiting_payment:
        return redirect(order)

    if request.method == 'POST':
        if request.POST.get('action') == 'pay':
            order.mark_paid(payment_id=f'TEST-{order.number}')
            send_order_email(request, order, 'paid')
            messages.success(request, 'Płatność testowa przyjęta. Dziękujemy za zamówienie!')
        else:
            order.cancel()
            messages.error(request, 'Płatność anulowana — zamówienie nie zostało opłacone.')
        return redirect(order)

    return render(request, 'shop/payment_dummy.html', {'order': order})
