from django.urls import path
from inventario import views

urlpatterns = [
    path('movimiento_inventario/', views.movimiento_inventario, name='movimiento_inventario'),
    path('confirmar_recepcion/', views.confirmar_recepcion, name='confirmar_recepcion'),
    path('confirmar_recepcion/<int:pk>/', views.confirmar_recepcion_detalle, name='confirmar_recepcion_detalle'),
    path('listado_movimientos/', views.movimiento_inventario, name='listado_movimientos'),
    path('producto_movimientos/', views.movimiento_inventario, name='movimiento_por_producto'),
    path('empresa_movimientos/', views.movimiento_inventario, name='movimiento_por_empresa'),
    path('sucursal_movimientos/', views.movimiento_inventario, name='movimiento_por_sucursal'),
]
