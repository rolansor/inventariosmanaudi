from django import forms
from models import MovimientoInventario


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
        cleaned_data = super().clean()
        tipo_movimiento = cleaned_data.get('tipo_movimiento')
        sucursal = cleaned_data.get('sucursal')
        sucursal_destino = cleaned_data.get('sucursal_destino')

        if tipo_movimiento == 'traslado' and sucursal == sucursal_destino:
            raise forms.ValidationError("La sucursal de destino no puede ser la misma que la sucursal de origen.")

        return cleaned_data