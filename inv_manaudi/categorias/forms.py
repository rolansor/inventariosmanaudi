from django import forms
from .models import Subcategoria, Categoria, Clase


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['codigo', 'nombre']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: A01',
                'pattern': '[A-Za-z0-9]{3}',
                'title': 'Código de 3 caracteres alfanuméricos',
                'maxlength': '3',
                'style': 'text-transform: uppercase;'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría',
                'maxlength': '255',
                'style': 'text-transform: uppercase;'

            })
        }


class SubcategoriaForm(forms.ModelForm):
    class Meta:
        model = Subcategoria
        fields = ['codigo', 'nombre']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: B01',
                'pattern': '[A-Za-z0-9]{3}',
                'title': 'Código de 3 caracteres alfanuméricos',
                'maxlength': '3',
                'style': 'text-transform: uppercase;'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la subcategoría',
                'maxlength': '255',
                'style': 'text-transform: uppercase;'
            })
        }


class ClaseForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = ['codigo', 'nombre']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: C01',
                'pattern': '[A-Za-z0-9]{3}',
                'title': 'Código de 3 caracteres alfanuméricos',
                'maxlength': '3',
                'style': 'text-transform: uppercase;'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la clase',
                'maxlength': '255',
                'style': 'text-transform: uppercase;'
            })
        }