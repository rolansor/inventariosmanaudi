from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    # Aquí puedes personalizar el admin del modelo Usuario
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('telefono', 'direccion')}),
    )

admin.site.register(Usuario, UsuarioAdmin)
