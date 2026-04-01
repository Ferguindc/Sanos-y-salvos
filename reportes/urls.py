from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), 
    path('mapa/', views.mapa, name='mapa'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('crear_reporte/', views.crear_reporte, name='crear_reporte'),
]