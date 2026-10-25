"""Admin de Django para la clasificación Categoría / Subcategoría / Clase."""
from django.contrib import admin
from .models import Categoria, Subcategoria, Clase


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Categorías filtrables por empresa."""
    list_display = ('codigo', 'nombre', 'empresa')
    search_fields = ('codigo', 'nombre', 'empresa__nombre')
    list_filter = ('empresa',)


@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    """Subcategorías filtrables por categoría."""
    list_display = ('codigo', 'nombre', 'categoria')
    search_fields = ('codigo', 'nombre', 'categoria__nombre', 'categoria__codigo')
    list_filter = ('categoria',)


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    """Clases con columna adicional de categoría."""
    list_display = ('codigo', 'nombre', 'subcategoria', 'get_categoria')
    search_fields = ('codigo', 'nombre', 'subcategoria__nombre', 'subcategoria__codigo', 'subcategoria__categoria__nombre')
    list_filter = ('subcategoria__categoria', 'subcategoria')

    @admin.display(description='Categoría', ordering='subcategoria__categoria__nombre')
    def get_categoria(self, obj):
        """Columna con el nombre de la categoría (dos niveles arriba)."""
        return obj.subcategoria.categoria.nombre
