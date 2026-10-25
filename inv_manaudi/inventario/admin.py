"""
Admin de Django para la app ``inventario``.

Solo se registra ``Inventario`` (consulta de saldos). ``MovimientoInventario`` y
``Traslado`` no se exponen a propósito: editarlos desde el admin no recalcula el stock
(ver ``MovimientoInventario.save``), por lo que toda operación debe hacerse desde las
pantallas de la aplicación.
"""
from django.contrib import admin
from .models import Inventario


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    """Consulta de saldos por sucursal y producto."""
    list_display = ('sucursal', 'producto', 'cantidad', 'stock_minimo', 'ultima_actualizacion')
    search_fields = ('sucursal__nombre', 'producto__nombre', 'producto__codigo')
    list_filter = ('sucursal',)
