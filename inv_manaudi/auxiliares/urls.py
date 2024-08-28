from django.urls import path
from . import views

urlpatterns = [
    path('consulta_id/', views.consulta_id, name='consulta_id'),
]
