from django.contrib import admin
from django.urls import path, include
from usuarios.views import inicio

urlpatterns = [
    path('', inicio, name='inicio'),
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('auxiliares/', include('auxiliares.urls')),
    path('inventario/', include('inventario.urls')),
]
