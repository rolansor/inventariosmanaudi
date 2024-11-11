from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django import forms
from .models import Usuario, UsuarioPerfil, Empresa, Sucursal


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'email')
    search_fields = ('nombre', 'direccion', 'telefono', 'email')
    ordering = ('nombre',)  # Ordenar por nombre por defecto

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'direccion', 'abreviatura', 'telefono')
    search_fields = ('nombre', 'empresa__nombre', 'direccion', 'abreviatura', 'telefono')
    list_filter = ('empresa',)  # Filtro por empresa
    ordering = ('empresa',)  # Ordenar por nombre de sucursal
    autocomplete_fields = ('empresa',)  # Agregar autocompletado para empresas

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('telefono', 'direccion')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'telefono')  # Mostrar teléfono en lista
    search_fields = ('username', 'email', 'telefono')
    list_filter = ('is_active', 'is_staff', 'is_superuser')  # Filtros adicionales
    ordering = ('username',)  # Ordenar por nombre de usuario

@admin.register(UsuarioPerfil)
class UsuarioPerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empresa', 'sucursal')
    search_fields = ('usuario__username', 'empresa__nombre', 'sucursal__nombre')
    list_filter = ('empresa', 'sucursal')  # Filtros de empresa y sucursal
    autocomplete_fields = ('usuario', 'empresa', 'sucursal')  # Habilitar autocompletado para relaciones
    ordering = ('empresa',)  # Ordenar por usuario


# Formulario de administración de grupos con usuarios
class GroupAdminForm(forms.ModelForm):
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


# Configuración personalizada de GroupAdmin
class CustomGroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm
    list_display = ['name']
    search_fields = ['name']


# Registrar el Group con el GroupAdmin personalizado
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
