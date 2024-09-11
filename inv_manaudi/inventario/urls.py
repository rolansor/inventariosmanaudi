from django.urls import path
from . import views

urlpatterns = [
    path('empresas/', views.empresa_list, name='empresa_list'),
    path('empresas/editar/<int:pk>/', views.empresa_edit, name='empresa_edit'),
    path('empresas/eliminar/<int:pk>/', views.empresa_delete, name='empresa_delete'),
    path('empresas/<int:pk>/sucursales', views.sucursal_list, name='sucursal_list'),
    path('sucursales/editar/<int:pk>/', views.sucursal_edit, name='sucursal_edit'),
    path('sucursales/eliminar/<int:pk>/', views.sucursal_delete, name='sucursal_delete'),


    path('nueva_categoria/', views.nueva_categoria, name='nueva_categoria'),
    path('lista_categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('categorias/<int:pk>/nueva_subcategoria/', views.nueva_subcategoria, name='nueva_subcategoria'),
    path('categorias/<int:pk>/lista_subcategorias/', views.lista_subcategorias, name='lista_subcategorias'),
    path('categorias/subcategorias/editar/<int:pk>/', views.editar_subcategoria, name='editar_subcategoria'),
    path('categorias/subcategorias/eliminar/<int:pk>/', views.eliminar_subcategoria, name='eliminar_subcategoria'),


    path('productos/', views.producto_list, name='producto_list'),
    path('productos/editar/<int:pk>/', views.producto_edit, name='producto_edit'),
    path('productos/eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),
    path('movimientos/', views.movimiento_inventario, name='movimiento_inventario'),
    path('lista_movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('consulta_producto/', views.consulta_producto, name='consulta_producto'),
    path('movimientos_producto/<int:producto_id>/', views.movimientos_producto, name='movimientos_producto'),
    path('buscar_productos_por_sucursal/<int:empresa_id>/<str:sucursal_id>/', views.buscar_productos_por_sucursal,
         name='buscar_productos_por_sucursal'),
    path('productos_sucursales/', views.productos_sucursales, name='productos_sucursales'),
    path('sucursales_por_empresa/<int:empresa_id>/', views.sucursales_por_empresa,
         name='sucursales_por_empresa'),
    path('productos_por_sucursal/<int:sucursal_id>/', views.productos_por_sucursal,
         name='productos_por_sucursal'),
]
