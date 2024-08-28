from django.urls import path
from . import views

urlpatterns = [
    path('empresas/', views.empresa_list, name='empresa_list'),
    path('empresas/editar/<int:pk>/', views.empresa_edit, name='empresa_edit'),
    path('empresas/eliminar/<int:pk>/', views.empresa_delete, name='empresa_delete'),
]
