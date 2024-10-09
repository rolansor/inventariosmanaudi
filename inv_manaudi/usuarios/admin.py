from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, UsuarioPerfil


# Registro del modelo Usuario
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('telefono', 'direccion')}),
    )


admin.site.register(Usuario, UsuarioAdmin)


# Registro del modelo UsuarioPerfil
class UsuarioPerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empresa', 'sucursal')
    list_filter = ('empresa', 'sucursal')


admin.site.register(UsuarioPerfil, UsuarioPerfilAdmin)

