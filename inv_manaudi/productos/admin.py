from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'marca', 'modelo', 'linea', 'sublinea', 'clase', 'precio', 'tipo_producto', 'estado')
    search_fields = ('codigo', 'marca', 'modelo')
    list_filter = ('linea', 'sublinea', 'clase', 'tipo_producto', 'material', 'estado')
    readonly_fields = ('codigo',)
