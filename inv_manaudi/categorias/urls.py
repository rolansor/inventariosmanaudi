from django.urls import path
from . import views

urlpatterns = [

    path('nueva_categoria/', views.nueva_categoria, name='nueva_categoria'),
    path('lista_categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('categorias/<int:pk>/nueva_subcategoria/', views.nueva_subcategoria, name='nueva_subcategoria'),
    path('categorias/<int:pk>/lista_subcategorias/', views.lista_subcategorias, name='lista_subcategorias'),
    path('categorias/subcategorias/editar/<int:pk>/', views.editar_subcategoria, name='editar_subcategoria'),
    path('categorias/subcategorias/eliminar/<int:pk>/', views.eliminar_subcategoria, name='eliminar_subcategoria'),
]
