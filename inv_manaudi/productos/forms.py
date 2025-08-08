from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    # Campo para mostrar el código generado (solo lectura)
    codigo_generado = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'placeholder': 'Se generará automáticamente'
        }),
        label='Código'
    )
    
    class Meta:
        model = Producto
        fields = ['linea', 'sublinea', 'clase', 'marca', 'modelo', 
                  'precio', 'tipo_producto', 'material', 'nombre', 'descripcion']
        widgets = {
            'linea': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'actualizarCodigo()',
                'required': 'required'
            }),
            'sublinea': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'actualizarCodigo()',
                'required': 'required'
            }),
            'clase': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'actualizarCodigo()',
                'required': 'required'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'text-transform: uppercase;',
                'oninput': 'this.value = this.value.toUpperCase()',
                'required': 'required'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'text-transform: uppercase;',
                'oninput': 'this.value = this.value.toUpperCase()',
                'required': 'required'
            }),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'required': 'required'
            }),
            'tipo_producto': forms.Select(attrs={'class': 'form-select'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'linea': 'Línea',
            'sublinea': 'Sublínea',
            'clase': 'Clase',
            'marca': 'Marca',
            'modelo': 'Modelo',
            'precio': 'Precio',
            'tipo_producto': 'Tipo',
            'material': 'Material',
            'nombre': 'Nombre (Opcional)',
            'descripcion': 'Descripción (Opcional)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Establecer campos requeridos
        self.fields['linea'].required = True
        self.fields['sublinea'].required = True
        self.fields['clase'].required = True
        self.fields['marca'].required = True
        self.fields['modelo'].required = True
        self.fields['precio'].required = True
        
        # Campos opcionales
        self.fields['descripcion'].required = False
        self.fields['nombre'].required = False
        self.fields['material'].required = False
        
        # Si es edición, mostrar el código actual
        if self.instance and self.instance.pk:
            self.fields['codigo_generado'].initial = self.instance.codigo
