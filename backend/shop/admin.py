from django.contrib import admin
from django.utils.html import format_html

from .emails import send_order_email
from .models import Category, Order, OrderItem, Product, ShippingMethod


def thumbnail(image, size):
    if not image:
        return '—'
    return format_html('<img src="{}" alt="" style="width:{}px;height:{}px;object-fit:cover;" />', image.url, size, size)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('image_small', 'name', 'category', 'price', 'sale_price', 'is_active', 'order')
    list_display_links = ('image_small', 'name')
    list_filter = ('category', 'is_active')
    list_editable = ('price', 'sale_price', 'is_active', 'order')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('image_large',)
    fields = (
        'name', 'slug', 'category', 'description', 'price', 'sale_price',
        'image', 'image_large', 'sizes', 'badge', 'is_active', 'order',
    )

    @admin.display(description='zdjęcie')
    def image_small(self, obj):
        return thumbnail(obj.image, 48)

    @admin.display(description='podgląd zdjęcia')
    def image_large(self, obj):
        return thumbnail(obj.image, 240)


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active', 'order')
    list_editable = ('price', 'is_active', 'order')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ('name', 'size', 'unit_price', 'quantity')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'created_at', 'full_name', 'customer', 'total', 'status', 'payment_provider')
    list_filter = ('status', 'payment_provider')
    search_fields = ('full_name', 'email', 'phone', 'user__email')
    date_hierarchy = 'created_at'
    inlines = (OrderItemInline,)
    actions = ('mark_shipped',)
    readonly_fields = (
        'user', 'shipping_name', 'shipping_price', 'total',
        'payment_provider', 'payment_id', 'created_at', 'paid_at',
    )
    fieldsets = (
        (None, {'fields': ('status', 'user', 'created_at')}),
        ('Odbiorca', {'fields': ('full_name', 'email', 'phone', 'street', 'postal_code', 'city', 'note')}),
        ('Kwoty', {'fields': ('shipping_name', 'shipping_price', 'total')}),
        ('Płatność', {'fields': ('payment_provider', 'payment_id', 'paid_at')}),
    )

    # Zamówienia powstają tylko przez sklep
    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ręczna zmiana statusu w formularzu też wysyła maila o wysyłce
        if 'status' in form.changed_data and obj.status == Order.Status.SHIPPED:
            send_order_email(request, obj, 'shipped')

    @admin.display(description='numer', ordering='pk')
    def number(self, obj):
        return obj.number

    @admin.display(description='konto', ordering='user')
    def customer(self, obj):
        return obj.user or 'gość'

    @admin.action(description='Oznacz jako wysłane (tylko opłacone)')
    def mark_shipped(self, request, queryset):
        orders = list(queryset.filter(status=Order.Status.PAID).prefetch_related('items'))
        for order in orders:
            order.status = Order.Status.SHIPPED
            order.save(update_fields=['status'])
            send_order_email(request, order, 'shipped')
        self.message_user(request, f'Oznaczono jako wysłane: {len(orders)}. Klienci dostali maila.')
