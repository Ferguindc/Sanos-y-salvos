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
    path('api/chat/mensajes/<int:reporte_id>/', views.obtener_mensajes, name='obtener_mensajes'),
    path('api/chat/enviar/<int:reporte_id>/', views.enviar_mensaje, name='enviar_mensaje'),
    path('api/razas/', views.obtener_razas, name='obtener_razas'),
    # Nuevos endpoints de matching
    path('api/mis-matches/', views.obtener_mis_matches, name='obtener_mis_matches'),
    path('api/match/<int:match_id>/confirmar/', views.confirmar_match, name='confirmar_match'),
    path('api/match/<int:match_id>/desmentir/', views.desmentir_match, name='desmentir_match'),
    path('api/admin/ejecutar-matching/', views.ejecutar_matching_manual, name='ejecutar_matching_manual'),
]
