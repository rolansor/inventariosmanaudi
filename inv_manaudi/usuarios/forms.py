"""Formularios de empresas y sucursales (pantallas de administración de Manaudi)."""
from django import forms
from .models import Empresa, Sucursal


class EmpresaForm(forms.ModelForm):
    """Alta y edición de empresas. Se envía por AJAX desde ``empresas.html``."""

    class Meta:
        model = Empresa
        fields = ['nombre', 'direccion', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class SucursalForm(forms.ModelForm):
    """
    Alta y edición de sucursales. Se envía por AJAX desde ``sucursales.html``.

    La empresa no es un campo del formulario: la vista ``sucursal_list`` la asigna a
    partir de la URL (``/usuarios/empresas/<pk>/sucursales``).
    """

    class Meta:
        model = Sucursal
        fields = ['nombre', 'abreviatura', 'tipo_sucursal', 'direccion', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'abreviatura': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'tipo_sucursal': forms.Select(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }
