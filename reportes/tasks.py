"""
Tareas en background para ejecutar matching automático
Usa APScheduler para ejecutarse periódicamente
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler.schedulers import DjangoScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from .matching_engine import ejecutar_matching_global, buscar_matches_para_reporte
from .notifications import notificar_match
from .models import PosibleMatch, ReporteMascota

logger = logging.getLogger(__name__)


def ejecutar_matching_task():
    """
    Tarea que ejecuta el matching automático
    Se ejecuta periódicamente según la configuración de APScheduler
    """
    try:
        print("🔄 Iniciando tarea de matching automático...")

        # Ejecutar matching global
        stats = ejecutar_matching_global()

        print(f"✅ Tarea completada:")
        print(f"   Reportes procesados: {stats['reportes_procesados']}")
        print(f"   Matches creados: {stats['matches_creados']}")

        # Notificar matches no notificados
        matches_sin_notificar = PosibleMatch.objects.filter(notificado=False)

        for match in matches_sin_notificar:
            try:
                notificar_match(
                    match.reporte_perdido,
                    match.reporte_encontrado,
                    match.score_similitud,
                    match.razon_match
                )
                stats['matches_notificados'] += 1
            except Exception as e:
                print(f"Error notificando match {match.id}: {str(e)}")

        print(f"   Matches notificados: {stats['matches_notificados']}")

        # Registrar ejecución exitosa
        DjangoJobExecution.objects.create(
            job_id='matching_task',
            status='success'
        )

    except Exception as e:
        logger.error(f"Error en tarea de matching: {str(e)}")
        DjangoJobExecution.objects.create(
            job_id='matching_task',
            status='failed',
            exc_message=str(e)
        )


def inicializar_scheduler():
    """
    Inicializa el scheduler de APScheduler
    Esta función se llama cuando Django inicia
    """
    scheduler = BackgroundScheduler()

    # Ejecutar matching 4 veces al día (cada 6 horas)
    scheduler.add_job(
        ejecutar_matching_task,
        trigger=CronTrigger(hour="*/6"),  # Cada 6 horas
        id='matching_task_periodic',
        name='Matching automático de mascotas',
        replace_existing=True,
    )

    # Limpiar ejecuciones antiguas 1 vez al día
    scheduler.add_job(
        limpiar_django_jobs,
        trigger=CronTrigger(hour=3, minute=0),  # A las 3 AM
        id='cleanup_jobs_task',
        name='Limpiar registros de trabajos completados',
        replace_existing=True,
    )

    scheduler.start()
    print("✅ APScheduler iniciado")


def limpiar_django_jobs():
    """
    Limpia el historial de ejecuciones completadas (más de 30 días)
    Para mantener la base de datos limpia
    """
    fecha_limite = timezone.now() - timedelta(days=30)
    DjangoJobExecution.objects.filter(created__lt=fecha_limite).delete()
    print("🧹 Historial de trabajos limpiado")


# Clase para management command (opcional)
class matching_task_command(BaseCommand):
    """
    Management command para ejecutar matching manualmente
    Uso: python manage.py runtask matching
    """

    help = 'Ejecuta el matching automático manualmente'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Ejecutando tarea de matching...'))
        ejecutar_matching_task()
        self.stdout.write(self.style.SUCCESS('✅ Tarea completada'))
