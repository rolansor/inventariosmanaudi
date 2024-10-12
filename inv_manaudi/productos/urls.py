from django.urls import path
from productos import views

urlpatterns = [
    path('productos/', views.producto_list, name='producto_list'),
    path('productos/editar/<int:pk>/', views.producto_edit, name='producto_edit'),
    path('productos/eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),
    path('consulta_producto/', views.consulta_producto, name='consulta_producto'),
]
