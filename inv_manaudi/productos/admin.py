from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'modelo', 'nombre', 'tipo_producto', 'precio', 'clase')
    search_fields = ('codigo', 'modelo', 'nombre', 'clase__nombre')
    list_filter = ('tipo_producto', 'clase', 'modelo')
