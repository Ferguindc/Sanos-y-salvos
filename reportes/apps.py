from django.apps import AppConfig


class ReportesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reportes'

    def ready(self):
        """
        Se ejecuta cuando Django inicia
        Inicializa el scheduler de tareas en background
        """
        try:
            from .tasks import inicializar_scheduler
            # Usar un flag para evitar inicializar dos veces
            import os
            if os.environ.get('RUN_MAIN', None) != 'true':
                inicializar_scheduler()
        except Exception as e:
            print(f"Error inicializando scheduler: {str(e)}")
