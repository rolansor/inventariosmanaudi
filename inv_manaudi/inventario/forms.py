from django import forms

from productos.models import Producto
from usuarios.models import Sucursal
from .models import MovimientoInventario


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['sucursal', 'producto', 'tipo_movimiento', 'cantidad', 'sucursal_destino', 'comentario', 'documento_respaldo', 'documento_traslado']
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'sucursal_destino': forms.Select(attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'documento_respaldo': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'documento_traslado': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        # Llamamos al método clean() del padre para obtener los datos ya limpiados
        cleaned_data = super().clean()
        tipo_movimiento = cleaned_data.get('tipo_movimiento')
        sucursal = cleaned_data.get('sucursal')
        sucursal_destino = cleaned_data.get('sucursal_destino')
        cantidad = cleaned_data.get('cantidad')

        # Validación de que la sucursal de origen y destino no sean la misma
        if tipo_movimiento == 'traslado' and sucursal == sucursal_destino:
            raise forms.ValidationError("La sucursal de destino no puede ser la misma que la sucursal de origen.")

        # Validación de que la cantidad sea un número entero positivo
        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser un número entero positivo.")

        return cleaned_data


class ConfirmarRecepcionForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['cantidad_recibida']
        widgets = {
            'cantidad_recibida': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_cantidad_recibida(self):
        cantidad_recibida = self.cleaned_data['cantidad_recibida']
        if cantidad_recibida <= 0:
            raise forms.ValidationError("La cantidad recibida debe ser un número positivo.")
        if cantidad_recibida > self.instance.cantidad:
            raise forms.ValidationError(f"La cantidad recibida no puede ser mayor que la cantidad enviada ({self.instance.cantidad}).")
        return cantidad_recibida


class ProductoSelectForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(),  # Inicialmente vacío, se llenará en el __init__
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label='Seleccione un producto'
    )

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)  # Obtener la empresa pasada en los kwargs
        super(ProductoSelectForm, self).__init__(*args, **kwargs)

        if empresa:
            # Filtrar productos que pertenezcan a la empresa
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)


class SucursalSelectForm(forms.Form):
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.none(),  # Inicialmente vacío, se llenará en el __init__
        widget=forms.Select(attrs={'class': 'select2 form-control'}),
        label="Seleccione una sucursal"
    )

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)  # Obtener la empresa pasada en los kwargs
        super(SucursalSelectForm, self).__init__(*args, **kwargs)

        if empresa:
            # Filtrar sucursales que pertenezcan a la empresa
            self.fields['sucursal'].queryset = Sucursal.objects.filter(empresa=empresa)
