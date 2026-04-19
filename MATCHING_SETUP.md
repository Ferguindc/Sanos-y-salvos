# 🎯 Sistema de Matching Automático - Guía de Configuración

## ✅ Lo que ya está implementado

✅ **Backend Core:**
- Modelo `PosibleMatch` para almacenar posibles coincidencias
- Integración con OpenAI Vision API para análisis de imágenes
- Motor de matching intelligent (matching_engine.py) con scoring multi-factor
- Sistema de notificaciones por Email + App
- Tareas en background automáticas con APScheduler

✅ **API Endpoints:**
- `GET /api/mis-matches/` - Ver mis posibles matches
- `POST /api/match/<id>/confirmar/` - Confirmar un match
- `POST /api/match/<id>/desmentir/` - Rechazar un match
- `POST /api/admin/ejecutar-matching/` - Ejecutar matching manualmente (admin)

✅ **Archivos creados:**
- `/reportes/vision_service.py` - Análisis de imágenes
- `/reportes/matching_engine.py` - Motor de matching con algoritmo de scoring
- `/reportes/tasks.py` - Tareas en background
- `/reportes/notifications.py` - Sistema de notificaciones
- `/reportes/models.py` - Modelo PosibleMatch agregado
- `/reportes/templates/email_match.html` - Template de email

## 🔧 Configuración Necesaria

### 1. **Obtener OpenAI API Key**

1. Ve a https://platform.openai.com/api-keys
2. Inicia sesión o crea una cuenta
3. Click en "Create new secret key"
4. Copia la clave (comienza con `sk-`)
5. NO la compartas con nadie

### 2. **Configurar Email (Gmail)**

Para enviar emails desde la aplicación:

1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. Busca "Seguridad" en el menú izquierdo
3. Habilita "Verificación en dos pasos" si no lo está
4. Ve a https://myaccount.google.com/apppasswords
5. Selecciona "Mail" y "Windows Computer" (o tu dispositivo)
6. Copia la contraseña de 16 caracteres generada

### 3. **Configurar archivo .env**

Abre `/Sanos-y-salvos/.env` y actualiza:

```env
# OpenAI API Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxx

# Email (Gmail)
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx (la de 16 caracteres)
DEFAULT_FROM_EMAIL=noreply@sanosysalvos.com
```

## 🚀 Cómo funciona el Matching

### Algoritmo de Scoring (Flexible ≥50%)

**Componentes:**
- **Imagen (40%):** Análisis con OpenAI Vision API
  - Color del pelaje
  - Raza probable
  - Tamaño estimado
  - Características distintivas

- **Atributos (35%):** Coincidencia de datos
  - Tipo de animal
  - Raza
  - Color
  - Tamaño

- **Ubicación (15%):** Proximidad geográfica
  - 0.5km: 15 puntos (mismo lugar)
  - 2km: 12 puntos
  - 5km: 8 puntos
  - 10km: 4 puntos

- **Fecha (10%):** Proximidad temporal
  - Mismo día: 10 puntos
  - 1-3 días: 7 puntos
  - 7 días: 4 puntos
  - 30 días: 1 punto

**Score Total:** Mínimo 50 para notificar

### Ejecución Automática

El matching se ejecuta automáticamente:
- **4 veces al día** (cada 6 horas a las: 00:00, 06:00, 12:00, 18:00)
- Procesa todos los reportes de últimos 30 días
- Envía notificaciones automáticamente

### Ejecutar Manualmente (Testing)

Para ejecutar matching manualmente mientras desarrollas:

```bash
# Opción 1: Endpoint de admin
curl -X POST http://localhost:8000/api/admin/ejecutar-matching/ \
  -H "Authorization: Bearer token"

# Opción 2: Shell de Django
python manage.py shell
>>> from reportes.matching_engine import ejecutar_matching_global
>>> stats = ejecutar_matching_global()
>>> print(stats)
```

## 📧 Notificaciones

### Email
- Se envía cuando se encuentra un match ≥50%
- Template personalizado con link al reporte
- Notificación de confirmación cuando el usuario confirma match

### En la App
- Nueva sección "Posibles Coincidencias"
- Visible en menú de la página de mapa
- Muestra score de similitud y razón del match
- Botones para confirmar o rechazar

## 🧪 Testing

### 1. **Crear reportes de prueba:**

```python
# En shell de Django
from reportes.models import ReporteMascota
from django.contrib.auth.models import User

# Usuario de prueba
user = User.objects.first()

# Reporte perdido
ReporteMascota.objects.create(
    titulo="Perro Labrador Negro Perdido",
    descripcion="Se perdió el domingo en el parque",
    latitud=-33.45,
    longitud=-70.66,
    usuario=user,
    tipo_reporte='perdido',
    tipo_animal='Perro',
    color='Negro',
    raza_probable='Labrador',
    tamaño='grande'
)

# Reporte encontrado (misma zona)
ReporteMascota.objects.create(
    titulo="Perro Labrador Negro Encontrado",
    descripcion="Lo encontré cerca del parque",
    latitud=-33.451,
    longitud=-70.661,
    usuario=user,
    tipo_reporte='encontrado',
    tipo_animal='Perro',
    color='Negro',
    raza_probable='Labrador',
    tamaño='grande'
)
```

### 2. **Ejecutar matching:**

```python
from reportes.matching_engine import ejecutar_matching_global
stats = ejecutar_matching_global()
# Debería crear un match
```

### 3. **Verificar en la API:**

```bash
curl http://localhost:8000/api/mis-matches/
```

## 📊 Vista del Usuario

### En `/mapa/`
1. Click en el botón "🎯 Posibles Coincidencias" (nuevo en navbar)
2. Ver lista de matches ordenados por similitud
3. Cada match muestra:
   - Porcentaje de similitud
   - Foto de la mascota encontrada
   - Razón del match
   - Botones: ✅ Confirmar / ❌ No es

### Al Confirmar Match
- Se envía email al usuario que reportó como "encontrado"
- El match se marca como confirmado
- El propietario y quien encontró pueden contactarse

##⚠️ Consideraciones Importantes

### Costo de OpenAI
- GPT-4 Vision: ~$0.01-0.03 por imagen
- Recomendación: Analizar solo 1-2 imágenes por reporte
- Con muchos reportes, los costos pueden subir

### Privacidad
- Las imágenes se envían a OpenAI para análisis
- Considerada una API segura, pero revisa política de privacidad
- Para máxima privacidad local, considera modelos de ML locales (YOLO, FastRCNN)

### Escalabilidad
- SQLite está bien para testing
- Para producción, usar PostgreSQL + Redis para caché
- Considerar Celery para tareas más pesadas

##🐛 Troubleshooting

### "Error: OPENAI_API_KEY not found"
❌ Solución: Verifica que `.env` existe y tiene la clave correcta

### "Email no se envía"
❌ Solución:
- Verifica EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en `.env`
- Habilita acceso de "apps menos seguras" en Gmail (o usa app password)
- Prueba manualmente: `python manage.py shell` → `from django.core.mail import send_mail`

### "Scheduler no inicia"
❌ Solución:
- Revisa logs: `tail -f /tmp/server.log`
- APScheduler se inicia automáticamente en `apps.py`
- Si hay error, reinicia el servidor

### "Score demasiado bajo"
❌ Solución:
- El umbral está en 50% (flexible)
- Revisa detalles del scoring en `matching_engine.py`
- Puedes ajustar pesos de los componentes

## 🎓 Próximas Mejoras (Opcional)

1. **Modelos ML locales:** Usar YOLO/FastRCNN en lugar de OpenAI (privacidad + costo)
2. **Búsqueda manual:** Form de búsqueda para que usuarios busquen matches específicos
3. **Estadísticas:** Dashboard con métricas de matches exitosos
4. **Integración con redes sociales:** Compartir reportes en Facebook/WhatsApp
5. **Votación comunitaria:** Comunidad valida si un match es correcto
6. **Rastreo de mascotas:** Mapa de traslado del animal después de reportarse

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs: `python manage.py runserver`
2. Verifica que todas las variables `.env` están configuradas
3. Ejecuta migraciones: `python manage.py migrate`
4. Limpia caché: `python manage.py clear_cache` (si usa caché)

---

**¡Sistema listo para usar! 🎉**

Próximos pasos:
1. Configura `.env` con API keys
2. Inicia el servidor: `python manage.py runserver`
3. Crea algunos reportes de prueba
4. El matching se ejecutará automáticamente cada 6 horas
5. Mira los matches en "Posibles Coincidencias"
