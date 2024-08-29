from django.urls import path
from . import views

urlpatterns = [
    path('empresas/', views.empresa_list, name='empresa_list'),
    path('empresas/editar/<int:pk>/', views.empresa_edit, name='empresa_edit'),
    path('empresas/eliminar/<int:pk>/', views.empresa_delete, name='empresa_delete'),
    path('empresas/<int:pk>/sucursales', views.sucursal_list, name='sucursal_list'),
    path('sucursales/editar/<int:pk>/', views.sucursal_edit, name='sucursal_edit'),
    path('sucursales/eliminar/<int:pk>/', views.sucursal_delete, name='sucursal_delete'),
    path('categorias/', views.categoria_list, name='categoria_list'),
    path('categorias/editar/<int:pk>/', views.categoria_edit, name='categoria_edit'),
    path('categorias/eliminar/<int:pk>/', views.categoria_delete, name='categoria_delete'),
    path('categorias/<int:pk>/subcategorias/', views.subcategoria_list, name='subcategoria_list'),
    path('subcategorias/editar/<int:pk>/', views.subcategoria_edit, name='subcategoria_edit'),
    path('subcategorias/eliminar/<int:pk>/', views.subcategoria_delete, name='subcategoria_delete'),
    path('productos/', views.producto_list, name='producto_list'),
    path('productos/editar/<int:pk>/', views.producto_edit, name='producto_edit'),
    path('productos/eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),
]
