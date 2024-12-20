from django.contrib import admin
from django.urls import path, include
from usuarios.views import inicio
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', inicio, name='inicio'),
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('auxiliares/', include('auxiliares.urls')),
    path('inventario/', include('inventario.urls')),
    path('categorias/', include('categorias.urls')),
    path('productos/', include('productos.urls')),
    path('reportes/', include('reportes.urls')),

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
