from django import forms
from productos.models import Producto
from usuarios.models import Sucursal
from .models import MovimientoInventario, Traslado


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['sucursal', 'producto', 'tipo_movimiento', 'cantidad', 'comentario', 'documento_respaldo', 'documento_soporte']
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'documento_respaldo': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'documento_soporte': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser un número positivo.")
        return cantidad

    def clean_documento_traslado(self):
        documento_soporte = self.cleaned_data.get('documento_soporte')
        if documento_soporte and documento_soporte.size > 5 * 1024 * 1024:  # Limitar a 5MB
            raise forms.ValidationError("El documento de traslado no puede exceder 5 MB.")
        return documento_soporte


class TrasladoForm(forms.ModelForm):
    class Meta:
        model = Traslado
        fields = ['producto', 'sucursal_origen', 'sucursal_destino', 'cantidad', 'documento_respaldo', 'documento_soporte']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'sucursal_origen': forms.Select(attrs={'class': 'form-control'}),
            'sucursal_destino': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'documento_respaldo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'documento_soporte': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        sucursal_origen = cleaned_data.get('sucursal_origen')
        sucursal_destino = cleaned_data.get('sucursal_destino')
        cantidad = cleaned_data.get('cantidad')

        if sucursal_origen == sucursal_destino:
            raise forms.ValidationError("La sucursal de origen y destino no pueden ser la misma.")

        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser un número positivo.")

        return cleaned_data


class ConfirmarRecepcionForm(forms.ModelForm):
    class Meta:
        model = Traslado
        fields = ['cantidad']  # Campo para actualizar la cantidad recibida
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_cantidad(self):
        cantidad_recibida = self.cleaned_data.get('cantidad')
        if cantidad_recibida <= 0:
            raise forms.ValidationError("La cantidad recibida debe ser un número positivo.")

        # Comparar la cantidad recibida con la cantidad enviada
        if cantidad_recibida > self.instance.cantidad:
            raise forms.ValidationError(
                f"La cantidad recibida no puede ser mayor que la cantidad enviada ({self.instance.cantidad}).")

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
