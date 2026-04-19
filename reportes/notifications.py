"""
Sistema de notificaciones para matches de mascotas
Envía notificaciones por email y crea notificaciones en la aplicación
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import PosibleMatch


def enviar_email_match(reporte_perdido, reporte_encontrado, score):
    """
    Envía un email al usuario notificando un posible match

    Args:
        reporte_perdido (ReporteMascota): Reporte de mascota perdida
        reporte_encontrado (ReporteMascota): Reporte de mascota encontrada
        score (float): Porcentaje de similitud
    """
    usuario_perdido = reporte_perdido.usuario

    if not usuario_perdido or not usuario_perdido.email:
        return False

    try:
        contexto = {
            'usuario': usuario_perdido.first_name or usuario_perdido.username,
            'mascota_perdida': reporte_perdido.titulo,
            'mascota_encontrada': reporte_encontrado.titulo,
            'similitud': f"{score:.0f}",
            'url_reporte': f"http://localhost:8000/mapa/#reporte_{reporte_encontrado.id}",
        }

        # Intentar cargar template, si no existe usar texto plano
        try:
            html_message = render_to_string('email_match.html', contexto)
        except:
            html_message = f"""
            <h2>¡Posible match encontrado!</h2>
            <p>Hola {contexto['usuario']},</p>
            <p>Se encontró un posible match ({contexto['similitud']}% de similitud) para tu reporte:</p>
            <p><strong>{contexto['mascota_perdida']}</strong></p>
            <p>Con el reporte:</p>
            <p><strong>{contexto['mascota_encontrada']}</strong></p>
            <p><a href="{contexto['url_reporte']}">Ver reporte</a></p>
            """

        send_mail(
            subject=f'🐕 ¡Posible match encontrado! ({score:.0f}% similitud)',
            message=f'Se encontró un posible match para {contexto["mascota_perdida"]}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario_perdido.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True

    except Exception as e:
        print(f"Error enviando email: {str(e)}")
        return False


def notificar_match(reporte_perdido, reporte_encontrado, score, razon_match):
    """
    Crea una notificación de match y envía email

    Args:
        reporte_perdido (ReporteMascota): Reporte de mascota perdida
        reporte_encontrado (ReporteMascota): Reporte de mascota encontrada
        score (float): Porcentaje de similitud
        razon_match (str): Explicación del match

    Returns:
        PosibleMatch: El match creado/actualizado
    """

    # Obtener o crear match
    match, created = PosibleMatch.objects.get_or_create(
        reporte_perdido=reporte_perdido,
        reporte_encontrado=reporte_encontrado,
        defaults={
            'score_similitud': score,
            'razon_match': razon_match
        }
    )

    # Si es nuevo, enviar notificaciones
    if created and not match.notificado:
        # Enviar email
        email_enviado = enviar_email_match(reporte_perdido, reporte_encontrado, score)

        # Marcar como notificado
        match.notificado = True
        match.save()

        print(f"✅ Match notificado: {match.id} (Email: {'Enviado' if email_enviado else 'Error'})")

    return match


def enviar_notificacion_confirmacion(match_id):
    """
    Envía notificación cuando un usuario confirma un match

    Args:
        match_id (int): ID del PosibleMatch
    """
    try:
        match = PosibleMatch.objects.get(id=match_id)

        if not match.confirmado:
            return False

        usuario_encontrado = match.reporte_encontrado.usuario

        if not usuario_encontrado or not usuario_encontrado.email:
            return False

        contexto = {
            'usuario': usuario_encontrado.first_name or usuario_encontrado.username,
            'mascota_encontrada': match.reporte_encontrado.titulo,
            'mascota_recuperada': match.reporte_perdido.titulo,
            'propietario': match.reporte_perdido.usuario.first_name or match.reporte_perdido.usuario.username,
        }

        html_message = f"""
        <h2>🎉 ¡Tu reporte ayudó a encontrar una mascota!</h2>
        <p>Hola {contexto['usuario']},</p>
        <p>¡Excelentes noticias! El dueño de <strong>{contexto['mascota_recuperada']}</strong>
        ha confirmado que la mascota que reportaste como encontrada es la suya.</p>
        <p>El propietario ({contexto['propietario']}) será contactado pronto para la entrega de la mascota.</p>
        <p>¡Gracias por ayudar a reunir a esta mascota con su familia!</p>
        """

        send_mail(
            subject='🐕 ¡Tu reporte ayudó a reunir una mascota con su familia!',
            message='Tu reporte ayudó a encontrar una mascota perdida.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario_encontrado.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True

    except Exception as e:
        print(f"Error enviando notificación de confirmación: {str(e)}")
        return False
