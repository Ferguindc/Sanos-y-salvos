from django.urls import path
from . import views

urlpatterns = [
    path('', views.mapa, name='mapa'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout')
]