from django.contrib import admin
from models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo_producto', 'precio', 'categoria')
    search_fields = ('codigo', 'nombre', 'categoria__nombre')
    list_filter = ('tipo_producto', 'categoria')
