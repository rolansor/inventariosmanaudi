from django.urls import path
from . import views

urlpatterns = [
    path('reporte_diario/', views.reporte_movimientos_dia, name='reporte_movimientos_dia'),
    path('inventario_valorizado/', views.reporte_inventario_valorizado, name='reporte_inventario_valorizado'),
]
