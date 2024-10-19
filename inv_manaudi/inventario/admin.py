from django.contrib import admin
from .models import Inventario, MovimientoInventario


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('sucursal', 'producto', 'cantidad', 'stock_minimo', 'ultima_actualizacion')
    search_fields = ('sucursal__nombre', 'producto__nombre')
    list_filter = ('sucursal', 'producto')
