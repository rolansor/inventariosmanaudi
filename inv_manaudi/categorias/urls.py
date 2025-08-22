from django.urls import path
from categorias import views

urlpatterns = [
    # Categorías
    path('nueva_categoria/', views.nueva_categoria, name='nueva_categoria'),
    path('lista_categorias/', views.lista_categorias, name='lista_categorias'),
    path('editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # Subcategorías
    path('<int:pk>/nueva_subcategoria/', views.nueva_subcategoria, name='nueva_subcategoria'),
    path('<int:pk>/lista_subcategorias/', views.lista_subcategorias, name='lista_subcategorias'),
    path('subcategorias/editar/<int:pk>/', views.editar_subcategoria, name='editar_subcategoria'),
    path('subcategorias/eliminar/<int:pk>/', views.eliminar_subcategoria, name='eliminar_subcategoria'),
    
    # Clases
    path('subcategorias/<int:pk>/nueva_clase/', views.nueva_clase, name='nueva_clase'),
    path('subcategorias/<int:pk>/lista_clases/', views.lista_clases, name='lista_clases'),
    path('clases/editar/<int:pk>/', views.editar_clase, name='editar_clase'),
    path('clases/eliminar/<int:pk>/', views.eliminar_clase, name='eliminar_clase'),
]
