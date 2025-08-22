from django import forms
from categorias.models import Clase
from .models import Producto


class ProductoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            # Obtener todas las clases de la empresa
            clases = (Clase.objects.filter(subcategoria__categoria__empresa=empresa)
                     .select_related('subcategoria__categoria')
                     .order_by('subcategoria__categoria__codigo', 'subcategoria__codigo', 'codigo'))
            
            # Crear las opciones con formato personalizado
            choices = [('', '-- Seleccione Categoría / Subcategoría / Clase --')]
            for clase in clases:
                label = f"{clase.subcategoria.categoria.codigo} - {clase.subcategoria.categoria.nombre} / {clase.subcategoria.codigo} - {clase.subcategoria.nombre} / {clase.codigo} - {clase.nombre}"
                choices.append((clase.pk, label))
            
            self.fields['clase'].choices = choices
    
    class Meta:
        model = Producto
        fields = ['codigo', 'codigo_auxiliar', 'codigo_ean', 'nombre', 'descripcion', 'precio', 'tipo_producto', 'clase']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[A-Za-z0-9\-]+',
                'title': 'Solo letras, números y guiones'
            }),
            'codigo_auxiliar': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[A-Za-z0-9\-]*',
                'title': 'Solo letras, números y guiones'
            }),
            'codigo_ean': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[0-9]{13}',
                'maxlength': '13',
                'title': 'Debe ser exactamente 13 dígitos'
            }),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_producto': forms.Select(attrs={'class': 'form-control'}),
            'clase': forms.Select(attrs={'class': 'form-control select2'}),
        }
