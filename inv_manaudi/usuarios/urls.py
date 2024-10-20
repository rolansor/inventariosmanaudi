from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro, name='registro'),
    path('editar/', views.editar_usuario, name='editar_usuario'),
    path('empresas/', views.empresa_list, name='empresa_list'),
    path('empresas/editar/<int:pk>/', views.empresa_edit, name='empresa_edit'),
    path('empresas/eliminar/<int:pk>/', views.empresa_delete, name='empresa_delete'),
    path('empresas/<int:pk>/sucursales', views.sucursal_list, name='sucursal_list'),
    path('sucursales/editar/<int:pk>/', views.sucursal_edit, name='sucursal_edit'),
    path('sucursales/eliminar/<int:pk>/', views.sucursal_delete, name='sucursal_delete'),
]
