from django.contrib import admin
from .models import Inventario, MovimientoInventario


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('sucursal', 'producto', 'cantidad', 'stock_minimo', 'ultima_actualizacion')
    search_fields = ('sucursal__nombre', 'producto__nombre')
    list_filter = ('sucursal', 'producto')


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('tipo_movimiento', 'sucursal', 'producto', 'cantidad', 'sucursal_destino', 'fecha')
    search_fields = ('sucursal__nombre', 'producto__nombre', 'tipo_movimiento')
    list_filter = ('tipo_movimiento', 'fecha', 'sucursal', 'sucursal_destino')
    date_hierarchy = 'fecha'