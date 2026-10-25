"""
Admin de Django para la app ``usuarios``.

La gestión de usuarios (alta, contraseña, grupos y perfil) se hace únicamente desde
``/admin/``; la aplicación no tiene pantallas propias para ello. Flujo para dar de
alta un usuario:

1. ``Usuarios``: crear el usuario y asignarle grupos (Manaudi / Supervisor / Encargado / Auditor).
2. ``Perfiles de usuario``: crear su ``UsuarioPerfil`` con la empresa y, si aplica, la sucursal.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django import forms
from .models import Usuario, UsuarioPerfil, Empresa, Sucursal


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    """Listado de empresas."""
    list_display = ('nombre', 'direccion', 'telefono', 'email')
    search_fields = ('nombre', 'direccion', 'telefono', 'email')
    ordering = ('nombre',)


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    """Sucursales filtrables por empresa y tipo."""
    list_display = ('nombre', 'empresa', 'tipo_sucursal', 'abreviatura', 'direccion', 'telefono')
    search_fields = ('nombre', 'empresa__nombre', 'direccion', 'abreviatura', 'telefono')
    list_filter = ('empresa', 'tipo_sucursal')
    ordering = ('empresa',)
    autocomplete_fields = ('empresa',)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Usuario estándar de Django más los campos teléfono y dirección."""
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('telefono', 'direccion')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'telefono')
    search_fields = ('username', 'email', 'telefono')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    ordering = ('username',)


@admin.register(UsuarioPerfil)
class UsuarioPerfilAdmin(admin.ModelAdmin):
    """Perfiles: aquí se asigna empresa y sucursal a cada usuario."""
    list_display = ('usuario', 'empresa', 'sucursal')
    search_fields = ('usuario__username', 'empresa__nombre', 'sucursal__nombre')
    list_filter = ('empresa', 'sucursal')
    autocomplete_fields = ('usuario', 'empresa', 'sucursal')
    ordering = ('empresa',)


class GroupAdminForm(forms.ModelForm):
    """
    Formulario de grupo con un selector de usuarios.

    Permite asignar varios usuarios a un rol desde la pantalla del grupo, en lugar de
    entrar usuario por usuario.
    """
    users = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('Usuarios', is_stacked=False)
    )

    class Meta:
        model = Group
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def save(self, commit=True):
        group = super().save(commit=False)
        if commit:
            group.save()
        if group.pk:
            group.user_set.set(self.cleaned_data['users'])
            self.save_m2m()
        return group


class CustomGroupAdmin(admin.ModelAdmin):
    """Reemplaza el admin de grupos por defecto para incluir el selector de usuarios."""
    form = GroupAdminForm
    list_display = ['name']
    search_fields = ['name']


admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
