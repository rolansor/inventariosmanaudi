"""Admin de Django para el catálogo de productos."""
from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Catálogo filtrable por empresa, estado y tipo."""
    list_display = ('codigo', 'modelo', 'nombre', 'empresa', 'tipo_producto', 'precio', 'clase', 'estado')
    search_fields = ('codigo', 'codigo_auxiliar', 'codigo_ean', 'modelo', 'nombre', 'clase__nombre')
    list_filter = ('empresa', 'estado', 'tipo_producto')
