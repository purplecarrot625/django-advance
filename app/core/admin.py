from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models

class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users"""
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            _('Permissions'),
            {
                'fields': ('is_active', 'is_staff', 'is_superuser')
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    # add_fieldsets is used to add fields to the add user page
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
        'classes': ('wide',),
        'fields': ('email', 'password1', 'password2', 'name', 'is_active', 'is_staff', 'is_superuser')
        }),
    )

admin.site.register(models.User, UserAdmin)  # user the customized admin page
admin.site.register(models.Recipe)  # use the default admin page
admin.site.register(models.Tag)
admin.site.register(models.Ingredient)