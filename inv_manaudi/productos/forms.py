"""Formulario de alta y edición de productos."""
from django import forms
from categorias.models import Clase
from .models import Producto


class ProductoForm(forms.ModelForm):
    """
    Alta y edición de un producto.

    Recibe ``empresa`` como argumento extra para limitar el selector de clase a la
    clasificación de esa empresa. Las opciones se muestran como
    ``CAT - Nombre / SUB - Nombre / CLA - Nombre`` y se renderizan con Select2.
    La empresa del producto no es un campo: la asigna la vista.
    """

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        if empresa:
            clases = (Clase.objects.filter(subcategoria__categoria__empresa=empresa)
                      .select_related('subcategoria__categoria')
                      .order_by('subcategoria__categoria__codigo', 'subcategoria__codigo', 'codigo'))

            choices = [('', '-- Seleccione Categoría / Subcategoría / Clase --')]
            for clase in clases:
                label = (f"{clase.subcategoria.categoria.codigo} - {clase.subcategoria.categoria.nombre} / "
                         f"{clase.subcategoria.codigo} - {clase.subcategoria.nombre} / "
                         f"{clase.codigo} - {clase.nombre}")
                choices.append((clase.pk, label))

            self.fields['clase'].choices = choices

    class Meta:
        model = Producto
        fields = ['codigo', 'codigo_auxiliar', 'codigo_ean', 'modelo', 'nombre', 'descripcion', 'precio', 'tipo_producto', 'clase']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'[A-Za-z0-9\-]+',
                'title': 'Solo letras, números y guiones'
            }),
            'codigo_auxiliar': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'[A-Za-z0-9\-]*',
                'title': 'Solo letras, números y guiones'
            }),
            'codigo_ean': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[0-9]{13}',
                'maxlength': '13',
                'title': 'Debe ser exactamente 13 dígitos'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'list': 'modelos_list',  # datalist alimentado por obtener_modelos_unicos
                'placeholder': 'Ingrese el modelo del producto'
            }),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_producto': forms.Select(attrs={'class': 'form-control'}),
            'clase': forms.Select(attrs={'class': 'form-control select2'}),
        }
