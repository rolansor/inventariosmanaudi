from django import forms
from .models import Empresa, Sucursal, Categoria, Subcategoria, Producto, MovimientoInventario


class EmpresaForm(forms.ModelForm):
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
    class Meta:
        model = Sucursal
        fields = ['empresa', 'nombre', 'abreviatura', 'direccion', 'telefono']


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']


class SubcategoriaForm(forms.ModelForm):
    class Meta:
        model = Subcategoria
        fields = ['nombre']


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'precio', 'tipo_producto', 'categoria']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_producto': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['sucursal', 'producto', 'tipo_movimiento', 'cantidad', 'sucursal_destino', 'comentario']
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'sucursal_destino': forms.Select(attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_movimiento = cleaned_data.get('tipo_movimiento')
        sucursal = cleaned_data.get('sucursal')
        sucursal_destino = cleaned_data.get('sucursal_destino')

        if tipo_movimiento == 'traslado' and sucursal == sucursal_destino:
            raise forms.ValidationError("La sucursal de destino no puede ser la misma que la sucursal de origen.")

        return cleaned_data