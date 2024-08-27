from django.contrib import admin
from .models import Empresa, Sucursal, Categoria, Subcategoria, Producto, Inventario, MovimientoInventario

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'email', 'fecha_creacion')
    search_fields = ('nombre', 'direccion', 'telefono', 'email')

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'direccion', 'abreviatura', 'telefono')
    search_fields = ('nombre', 'empresa__nombre', 'direccion', 'abreviatura', 'telefono')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria')
    search_fields = ('nombre', 'categoria__nombre')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo_producto', 'precio', 'categoria')
    search_fields = ('codigo', 'nombre', 'categoria__nombre')
    list_filter = ('tipo_producto', 'categoria')

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