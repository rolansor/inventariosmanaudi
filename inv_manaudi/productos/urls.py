from django.urls import path
from productos import views

urlpatterns = [
    path('nuevo/', views.crear_producto, name='crear_producto'),
    path('lista_productos/', views.lista_productos, name='lista_productos'),
    path('busqueda/', views.busqueda_producto, name='busqueda_producto'),
    path('editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('eliminar/<int:pk>/', views.desactivar_producto, name='eliminar_producto'),
    path('desborrar/<int:pk>/', views.activar_producto, name='activar_producto'),
    path('bsq_por_codigo/', views.bsq_por_codigo, name='bsq_por_codigo'),
]
