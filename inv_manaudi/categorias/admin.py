from django.contrib import admin
from .models import Categoria, Subcategoria, Clase


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'empresa')
    search_fields = ('codigo', 'nombre', 'empresa__nombre')
    list_filter = ('empresa',)


@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria')
    search_fields = ('codigo', 'nombre', 'categoria__nombre', 'categoria__codigo')
    list_filter = ('categoria',)


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'subcategoria', 'get_categoria')
    search_fields = ('codigo', 'nombre', 'subcategoria__nombre', 'subcategoria__codigo', 'subcategoria__categoria__nombre')
    list_filter = ('subcategoria__categoria', 'subcategoria')
    
    def get_categoria(self, obj):
        return obj.subcategoria.categoria.nombre
    get_categoria.short_description = 'Categoría'
    get_categoria.admin_order_field = 'subcategoria__categoria__nombre'
