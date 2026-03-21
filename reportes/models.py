from django.db import models
from django.contrib import admin

# Create your models here.

class ReporteMascota(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='mascotas/', null=True, blank=True)
    
    latitud = models.FloatField()
    longitud = models.FloatField()
    
    fecha = models.DateTimeField(auto_now_add=True)

    tipo_animal = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    raza_probable = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.titulo
    


admin.site.register(ReporteMascota)