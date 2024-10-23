from django import forms
from productos.models import Producto
from usuarios.models import Sucursal
from .models import MovimientoInventario, Traslado


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['sucursal', 'producto', 'tipo_movimiento', 'tipo_documento', 'cantidad', 'comentario', 'documento_respaldo', 'documento_soporte']
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'documento_respaldo': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'documento_soporte': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user is not None:
            empresa = user.perfil.empresa
            sucursal = getattr(user.perfil, 'sucursal', None)

            if sucursal:
                # Limitar la sucursal del usuario y hacerla no editable
                self.fields['sucursal'].queryset = Sucursal.objects.filter(id=sucursal.id)
                self.fields['sucursal'].initial = sucursal
                self.fields['sucursal'].widget.attrs['readonly'] = True
            else:
                # Mostrar todas las sucursales de la empresa si no tiene una específica
                self.fields['sucursal'].queryset = Sucursal.objects.filter(empresa=empresa)

            # Limitar los productos a los de la empresa del usuario
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)

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

    # Validación del campo tipo_documento
    def clean_tipo_documento(self):
        tipo_documento = self.cleaned_data.get('tipo_documento')
        if not tipo_documento:
            raise forms.ValidationError("El tipo de documento es obligatorio.")
        return tipo_documento

    # Validación del campo documento_respaldo
    def clean_documento_respaldo(self):
        documento_respaldo = self.cleaned_data.get('documento_respaldo')
        if not documento_respaldo:
            raise forms.ValidationError("El documento de respaldo es obligatorio.")
        return documento_respaldo


class TrasladoForm(forms.ModelForm):
    class Meta:
        model = Traslado
        fields = ['producto', 'sucursal_origen', 'sucursal_destino', 'cantidad_entregada', 'tipo_documento', 'documento_respaldo', 'documento_soporte']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'sucursal_origen': forms.Select(attrs={'class': 'form-control'}),
            'sucursal_destino': forms.Select(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_entregada': forms.NumberInput(attrs={'class': 'form-control'}),
            'documento_respaldo': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'documento_soporte': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        sucursal_origen = cleaned_data.get('sucursal_origen')
        sucursal_destino = cleaned_data.get('sucursal_destino')
        cantidad_entregada = cleaned_data.get('cantidad_entregada')

        if sucursal_origen == sucursal_destino:
            raise forms.ValidationError("La sucursal de origen y destino no pueden ser la misma.")

        if cantidad_entregada <= 0:
            raise forms.ValidationError("La cantidad entregada debe ser un número positivo.")

        return cleaned_data

        # Validación del campo tipo_documento
    def clean_tipo_documento(self):
        tipo_documento = self.cleaned_data.get('tipo_documento')
        if not tipo_documento:
            raise forms.ValidationError("El tipo de documento es obligatorio.")
        return tipo_documento

    # Validación del campo documento_respaldo
    def clean_documento_respaldo(self):
        documento_respaldo = self.cleaned_data.get('documento_respaldo')
        if not documento_respaldo:
            raise forms.ValidationError("El documento de respaldo es obligatorio.")
        return documento_respaldo


class ConfirmarRecepcionForm(forms.ModelForm):
    class Meta:
        model = Traslado
        fields = ['cantidad_recibida']  # Campo para actualizar la cantidad recibida
        widgets = {
            'cantidad_recibida': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_cantidad_recibida(self):
        cantidad_recibida = self.cleaned_data.get('cantidad_recibida')

        if cantidad_recibida <= 0:
            raise forms.ValidationError("La cantidad recibida debe ser un número mayor a 0.")

        # No se valida si es mayor que la cantidad entregada, como se acordó
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
