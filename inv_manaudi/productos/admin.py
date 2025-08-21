from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo_producto', 'precio', 'clase')
    search_fields = ('codigo', 'nombre', 'clase__nombre')
    list_filter = ('tipo_producto', 'clase')
