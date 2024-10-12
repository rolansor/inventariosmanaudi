from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, UsuarioPerfil, Empresa, Sucursal


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'email', 'fecha_creacion')
    search_fields = ('nombre', 'direccion', 'telefono', 'email')


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'direccion', 'abreviatura', 'telefono')
    search_fields = ('nombre', 'empresa__nombre', 'direccion', 'abreviatura', 'telefono')


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

