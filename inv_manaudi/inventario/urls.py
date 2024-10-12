from django.urls import path
from . import views

urlpatterns = [
    path('movimientos/', views.movimiento_inventario, name='movimiento_inventario'),
    path('lista_movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos_producto/<int:producto_id>/', views.movimientos_producto, name='movimientos_producto'),
    path('buscar_productos_por_sucursal/<int:empresa_id>/<str:sucursal_id>/', views.buscar_productos_por_sucursal,
         name='buscar_productos_por_sucursal'),
    path('productos_sucursales/', views.productos_sucursales, name='productos_sucursales'),
    path('sucursales_por_empresa/<int:empresa_id>/', views.sucursales_por_empresa,
         name='sucursales_por_empresa'),
    path('productos_por_sucursal/<int:sucursal_id>/', views.productos_por_sucursal,
         name='productos_por_sucursal'),
]
