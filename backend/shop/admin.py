from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'sale_price', 'is_active', 'order', 'has_buy_url')
    list_filter = ('category', 'is_active')
    list_editable = ('price', 'sale_price', 'is_active', 'order')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(boolean=True, description='link do zakupu')
    def has_buy_url(self, obj):
        return bool(obj.buy_url)
