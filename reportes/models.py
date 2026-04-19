from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

# Create your models here.

TIPO_REPORTE_CHOICES = [
    ('encontrado', 'Perrito Encontrado'),
    ('perdido', 'Busco Perrito Perdido'),
]

TAMAÑO_CHOICES = [
    ('pequeño', 'Pequeño'),
    ('mediano', 'Mediano'),
    ('grande', 'Grande'),
]


class ReporteMascota(models.Model):
    # Información básica
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()

    # Ubicación
    latitud = models.FloatField()
    longitud = models.FloatField()

    # Metadata
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Información del animal
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_REPORTE_CHOICES, default='encontrado')
    tipo_animal = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    raza_probable = models.CharField(max_length=100, blank=True)
    tamaño = models.CharField(max_length=20, choices=TAMAÑO_CHOICES, blank=True)

    def __str__(self):
        return self.titulo

    def get_imagenes(self):
        return self.imagenes.all()


class ImagenReporte(models.Model):
    reporte = models.ForeignKey(ReporteMascota, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='mascotas/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen de {self.reporte.titulo}"

    class Meta:
        ordering = ['-fecha_subida']


class MensajeChat(models.Model):
    reporte = models.ForeignKey(ReporteMascota, on_delete=models.CASCADE, related_name='mensajes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.reporte.titulo}"

    class Meta:
        ordering = ['fecha']


class PosibleMatch(models.Model):
    """Almacena posibles coincidencias entre reportes perdidos y encontrados"""

    reporte_perdido = models.ForeignKey(
        ReporteMascota,
        on_delete=models.CASCADE,
        related_name='matches_como_perdido',
        limit_choices_to={'tipo_reporte': 'perdido'}
    )
    reporte_encontrado = models.ForeignKey(
        ReporteMascota,
        on_delete=models.CASCADE,
        related_name='matches_como_encontrado',
        limit_choices_to={'tipo_reporte': 'encontrado'}
    )

    # Puntuación de similitud (0-100)
    score_similitud = models.FloatField(help_text="Porcentaje de similitud (0-100)")

    # Razón del match
    razon_match = models.TextField(help_text="Explicación de por qué estos reportes coinciden")

    # Estados
    confirmado = models.BooleanField(default=False, help_text="Usuario confirmó que es su mascota")
    desmentido = models.BooleanField(default=False, help_text="Usuario rechazó el match")
    notificado = models.BooleanField(default=False, help_text="Se envió notificación al usuario")

    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score_similitud', '-fecha_creacion']
        unique_together = ('reporte_perdido', 'reporte_encontrado')
        verbose_name_plural = "Posibles Matches"

    def __str__(self):
        return f"Match: {self.reporte_perdido.titulo} ↔ {self.reporte_encontrado.titulo} ({self.score_similitud:.0f}%)"


admin.site.register(ReporteMascota)
admin.site.register(ImagenReporte)
admin.site.register(MensajeChat)
admin.site.register(PosibleMatch)
