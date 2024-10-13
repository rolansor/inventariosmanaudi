from django.urls import path
from productos import views

urlpatterns = [
    path('nuevo/', views.crear_producto, name='crear_producto'),
    path('lista_productos/', views.lista_productos, name='lista_productos'),
    path('busqueda/', views.busqueda_producto, name='busqueda_producto'),

    path('productos/', views.producto_list, name='producto_list'),
    path('productos/editar/<int:pk>/', views.producto_edit, name='producto_edit'),
    path('productos/eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),
    path('consulta_producto/', views.consulta_producto, name='consulta_producto'),
]
