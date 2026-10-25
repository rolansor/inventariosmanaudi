"""
Formularios de la app ``inventario``.

- ``MovimientoInventarioForm``: entrada/salida de stock.
- ``TrasladoForm``: inicio de un traslado entre sucursales.
- ``ConfirmarRecepcionForm``: cantidad recibida al confirmar un traslado.
- ``ProductoSelectForm`` / ``SucursalSelectForm``: selectores para las consultas de
  movimientos por producto y por sucursal.

Todos reciben la empresa (y a veces la sucursal) del usuario para acotar los
``queryset`` de los selectores a la empresa activa.
"""
from django import forms
from productos.models import Producto
from usuarios.models import Sucursal
from .models import MovimientoInventario, Traslado

TAMANO_MAXIMO_DOCUMENTO = 5 * 1024 * 1024  # 5 MB


def validar_tamano_documento(documento):
    """Valida que el documento de soporte adjunto no supere ``TAMANO_MAXIMO_DOCUMENTO``."""
    if documento and documento.size > TAMANO_MAXIMO_DOCUMENTO:
        raise forms.ValidationError("El documento de soporte no puede exceder 5 MB.")
    return documento


class MovimientoInventarioForm(forms.ModelForm):
    """
    Registro de una entrada o salida de stock.

    Argumentos extra:

    - ``empresa``: limita productos y sucursales a la empresa activa.
    - ``sucursal``: si el usuario tiene sucursal asignada, el selector queda fijado en
      ella (solo puede mover stock de su propia sucursal).

    El número de documento de respaldo es obligatorio aunque el modelo lo permita vacío.
    """

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
        empresa = kwargs.pop('empresa', None)
        sucursal = kwargs.pop('sucursal', None)
        super().__init__(*args, **kwargs)

        if empresa is not None:
            if sucursal is not None:
                # Usuario con sucursal asignada: solo puede operar sobre ella
                self.fields['sucursal'].queryset = Sucursal.objects.filter(id=sucursal.id)
                self.fields['sucursal'].initial = sucursal
                self.fields['sucursal'].widget.attrs['readonly'] = True
            else:
                self.fields['sucursal'].queryset = Sucursal.objects.filter(empresa=empresa)

            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser un número positivo.")
        return cantidad

    def clean_documento_soporte(self):
        return validar_tamano_documento(self.cleaned_data.get('documento_soporte'))

    def clean_tipo_documento(self):
        tipo_documento = self.cleaned_data.get('tipo_documento')
        if not tipo_documento:
            raise forms.ValidationError("El tipo de documento es obligatorio.")
        return tipo_documento

    def clean_documento_respaldo(self):
        documento_respaldo = self.cleaned_data.get('documento_respaldo')
        if not documento_respaldo:
            raise forms.ValidationError("El # de documento de respaldo es obligatorio.")
        return documento_respaldo


class TrasladoForm(forms.ModelForm):
    """
    Inicio de un traslado. La vista acota productos y sucursales a la empresa activa.

    Valida que origen y destino sean distintos y que la cantidad sea positiva; la
    disponibilidad de stock en origen la valida el modelo al guardar.
    """

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

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if empresa is not None:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)
            self.fields['sucursal_origen'].queryset = Sucursal.objects.filter(empresa=empresa)
            self.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa)

    def clean(self):
        """Origen y destino deben ser distintos; la cantidad entregada debe ser positiva."""
        cleaned_data = super().clean()
        sucursal_origen = cleaned_data.get('sucursal_origen')
        sucursal_destino = cleaned_data.get('sucursal_destino')
        cantidad_entregada = cleaned_data.get('cantidad_entregada')

        if sucursal_origen is not None and sucursal_origen == sucursal_destino:
            raise forms.ValidationError("La sucursal de origen y destino no pueden ser la misma.")

        if cantidad_entregada is not None and cantidad_entregada <= 0:
            raise forms.ValidationError("La cantidad entregada debe ser un número positivo.")

        return cleaned_data

    def clean_documento_soporte(self):
        return validar_tamano_documento(self.cleaned_data.get('documento_soporte'))

    def clean_tipo_documento(self):
        tipo_documento = self.cleaned_data.get('tipo_documento')
        if not tipo_documento:
            raise forms.ValidationError("El tipo de documento es obligatorio.")
        return tipo_documento

    def clean_documento_respaldo(self):
        documento_respaldo = self.cleaned_data.get('documento_respaldo')
        if not documento_respaldo:
            raise forms.ValidationError("El documento de respaldo es obligatorio.")
        return documento_respaldo


class ConfirmarRecepcionForm(forms.ModelForm):
    """
    Cantidad realmente recibida al confirmar un traslado.

    Debe ser mayor a 0. Por decisión de negocio NO se exige que coincida con la
    cantidad entregada: la diferencia queda registrada y se muestra en los reportes.
    """

    class Meta:
        model = Traslado
        fields = ['cantidad_recibida']
        widgets = {
            'cantidad_recibida': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_cantidad_recibida(self):
        cantidad_recibida = self.cleaned_data.get('cantidad_recibida')
        if cantidad_recibida is None or cantidad_recibida <= 0:
            raise forms.ValidationError("La cantidad recibida debe ser un número mayor a 0.")
        return cantidad_recibida


class ProductoSelectForm(forms.Form):
    """Selector de producto (Select2) para la consulta de movimientos por producto."""
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(),  # se rellena en __init__ con la empresa
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label='Seleccione un producto'
    )

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)


class SucursalSelectForm(forms.Form):
    """Selector de sucursal (Select2) para la consulta de movimientos por sucursal."""
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.none(),  # se rellena en __init__ con la empresa
        widget=forms.Select(attrs={'class': 'select2 form-control'}),
        label="Seleccione una sucursal"
    )

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['sucursal'].queryset = Sucursal.objects.filter(empresa=empresa)
