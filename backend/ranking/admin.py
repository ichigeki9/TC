from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Count

from .models import DailyWorkout, Exercise, PartResult, Result, Workout, WorkoutPart


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 3


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    inlines = (ExerciseInline,)
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


class WorkoutPartInline(admin.StackedInline):
    model = WorkoutPart
    extra = 5
    fields = (('name', 'score_type', 'order'), 'description')
    formfield_overrides = {
        # Niższe pole opisu, żeby 5 części mieściło się na ekranie
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 3, 'cols': 80})},
    }


@admin.register(DailyWorkout)
class DailyWorkoutAdmin(admin.ModelAdmin):
    inlines = (WorkoutPartInline,)
    list_display = ('date', 'title', 'part_count', 'is_published')
    list_editable = ('is_published',)
    list_filter = ('is_published',)
    search_fields = ('title', 'parts__name')
    date_hierarchy = 'date'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(part_count=Count('parts'))

    @admin.display(description='części', ordering='part_count')
    def part_count(self, obj):
        return obj.part_count


@admin.register(PartResult)
class PartResultAdmin(admin.ModelAdmin):
    list_display = ('part', 'user', 'display_value', 'created_at')
    list_filter = ('part__daily__date',)
    search_fields = ('user__display_name', 'user__email', 'part__name')
    date_hierarchy = 'part__daily__date'
    autocomplete_fields = ('user',)
    list_select_related = ('part__daily', 'user')

    @admin.display(description='wynik')
    def display_value(self, obj):
        return obj.display_value
