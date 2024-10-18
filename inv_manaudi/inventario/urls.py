from django.urls import path
from inventario import views

urlpatterns = [
    path('movimiento_inventario/', views.movimiento_inventario, name='movimiento_inventario'),
    path('confirmar_recepcion/', views.confirmar_recepcion, name='confirmar_recepcion'),
    path('confirmar_recepcion/<int:pk>/', views.confirmar_recepcion_detalle, name='confirmar_recepcion_detalle'),
    path('producto_movimientos/', views.movimientos_por_producto, name='movimientos_por_producto'),
    path('empresa_movimientos/', views.movimientos_por_empresa, name='movimientos_por_empresa'),
    path('sucursal_movimientos/', views.movimientos_por_sucursal, name='movimientos_por_sucursal'),
]
