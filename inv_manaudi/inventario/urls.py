from django.urls import path
from inventario import views

urlpatterns = [
    path('movimiento_inventario/', views.movimiento_inventario, name='movimiento_inventario'),
    path('traslado/iniciar/', views.iniciar_traslado, name='iniciar_traslado'),
    path('traslado_laboratorio/iniciar/', views.iniciar_traslado_laboratorio, name='iniciar_traslado_laboratorio'),
    path('traslados_pendientes/', views.traslados_pendientes, name='traslados_pendientes'),
    path('traslado/confirmar/<int:pk>/', views.confirmar_traslado, name='confirmar_traslado'),
    path('producto_movimientos/', views.movimientos_por_producto, name='movimientos_por_producto'),
    path('empresa_movimientos/', views.movimientos_por_empresa, name='movimientos_por_empresa'),
    path('sucursal_movimientos/', views.movimientos_por_sucursal, name='movimientos_por_sucursal'),
]
