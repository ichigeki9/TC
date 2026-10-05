from django.contrib import admin

from shop.admin import thumbnail

from .models import Training


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('image_small', 'title', 'kind', 'date_text', 'place', 'is_active', 'order')
    list_display_links = ('image_small', 'title')
    list_filter = ('kind', 'is_active')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('image_large',)
    fieldsets = (
        (None, {'fields': ('kind', 'title', 'slug', 'icon', 'meta', 'badge')}),
        ('Treść', {'fields': ('description', 'points', 'image', 'image_large')}),
        ('Termin i cena', {'fields': ('date_text', 'place', 'price')}),
        ('Publikacja', {'fields': ('is_active', 'order')}),
    )

    @admin.display(description='zdjęcie')
    def image_small(self, obj):
        return thumbnail(obj.image, 48)

    @admin.display(description='podgląd zdjęcia')
    def image_large(self, obj):
        return thumbnail(obj.image, 240)
