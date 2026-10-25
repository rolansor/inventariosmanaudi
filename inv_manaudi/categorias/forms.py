"""
Formularios de categorías, subcategorías y clases.

Los tres son idénticos (código de 3 caracteres + nombre) y se envían por AJAX desde
los modales de ``lista_categorias.html``, ``lista_subcategorias.html`` y
``lista_clases.html``. El padre (empresa, categoría o subcategoría) lo asigna la vista.
"""
from django import forms
from .models import Subcategoria, Categoria, Clase


def _widgets(placeholder_codigo, placeholder_nombre):
    """Widgets Bootstrap comunes a los tres formularios (mayúsculas forzadas en pantalla)."""
    return {
        'codigo': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': placeholder_codigo,
            'pattern': '[A-Za-z0-9]{3}',
            'title': 'Código de 3 caracteres alfanuméricos',
            'maxlength': '3',
            'style': 'text-transform: uppercase;'
        }),
        'nombre': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': placeholder_nombre,
            'maxlength': '255',
            'style': 'text-transform: uppercase;'
        }),
    }


class CategoriaForm(forms.ModelForm):
    """Alta/edición de categoría. La empresa la asigna la vista."""

    class Meta:
        model = Categoria
        fields = ['codigo', 'nombre']
        widgets = _widgets('Ej: A01', 'Nombre de la categoría')


class SubcategoriaForm(forms.ModelForm):
    """Alta/edición de subcategoría. La categoría padre la asigna la vista."""

    class Meta:
        model = Subcategoria
        fields = ['codigo', 'nombre']
        widgets = _widgets('Ej: B01', 'Nombre de la subcategoría')


class ClaseForm(forms.ModelForm):
    """Alta/edición de clase. La subcategoría padre la asigna la vista."""

    class Meta:
        model = Clase
        fields = ['codigo', 'nombre']
        widgets = _widgets('Ej: C01', 'Nombre de la clase')
