from django.contrib import admin

from .models import Result, Workout


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'score_type', 'is_active', 'order')
    list_filter = ('program', 'score_type', 'is_active')
    list_editable = ('is_active', 'order')
    search_fields = ('name', 'program')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('workout', 'user', 'display_value', 'performed_on', 'created_at')
    list_filter = ('workout__program', 'workout')
    search_fields = ('user__display_name', 'user__email', 'workout__name')
    date_hierarchy = 'performed_on'
    autocomplete_fields = ('user',)

    @admin.display(description='wynik')
    def display_value(self, obj):
        return obj.display_value
