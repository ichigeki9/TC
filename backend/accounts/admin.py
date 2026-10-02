from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'display_name', 'gender', 'is_active', 'date_joined')
    list_filter = ('gender', 'is_active', 'is_staff')
    search_fields = ('email', 'display_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profil', {'fields': ('display_name', 'gender')}),
        ('Uprawnienia', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Daty', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'display_name', 'gender', 'password1', 'password2')}),
    )
