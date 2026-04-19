# 📋 Sistema de Reportes - Guía Completa

## ✅ Características Implementadas

### 1. **Tipos de Reporte** (Encontrado/Perdido)
- ✅ Los usuarios pueden elegir si reportan un perro **ENCONTRADO** 🐕 o **PERDIDO** 🔍
- ✅ El estado se muestra con badges coloreados en el modal
  - Verde (#27ae60): Perro Encontrado
  - Rojo (#e74c3c): Perro Perdido
- ✅ Los marcadores en el mapa tienen colores diferentes según el tipo

### 2. **The Dog API Integration** 🐕
- ✅ Selector dinámico de razas desde **The Dog API** (https://api.thedogapi.com)
- ✅ Sistema de fallback: Si la API no responde, usa lista alternativa de 23 razas
- ✅ Se carga automáticamente al abrir el formulario de reportes
- ✅ Notificación de confirmación cuando se cargan las razas

### 3. **Información del Animal**
- **Campos disponibles:**
  - Tipo de Animal (Perro, Gato, etc.)
  - Tamaño: Pequeño, Mediano, Grande
  - Color: Texto libre
  - Raza: Selector con+200 razas desde The Dog API

### 4. **Múltiples Imágenes**
- ✅ Máximo 5 imágenes por reporte
- ✅ 5MB máximo por imagen
- ✅ Drag & drop o click para subir
- ✅ Preview antes de enviar
- ✅ Botón para eliminar imágenes individuales
- ✅ Contador de imágenes seleccionadas

### 5. **Validaciones**
- ✅ Filtrado de contenido obsceno (15+ idiomas)
- ✅ Campos obligatorios: Título, Descripción, Color, Tamaño, Mínimo 1 imagen
- ✅ Validación en backend Y frontend
- ✅ Límite de 5MB por imagen

### 6. **Chat en Tiempo Real**
- ✅ Usuarios pueden chatear sobre cada reporte
- ✅ Tus mensajes en azul, otros en gris
- ✅ Muestra nombre de usuario y hora
- ✅ Auto scroll al último mensaje

### 7. **Notificaciones**
- ✅ Confirmación visual de éxito (verde) ✅
- ✅ Errores en rojo ❌
- ✅ Información en azul 💬
- ✅ Se desvanecen automáticamente en 4 segundos

## 🗄️ Estructura de Base de Datos

### **ReporteMascota**
```
- id (PK)
- titulo (max 100 chars)
- descripcion (texto largo)
- tipo_animal (perro, gato, etc.)
- color
- raza_probable (desde The Dog API)
- tamaño (pequeño, mediano, grande)
- tipo_reporte (encontrado / perdido)
- latitud, longitud (ubicación)
- usuario (FK a User)
- fecha (auto_now_add)
```

### **ImagenReporte**
```
- id (PK)
- reporte (FK a ReporteMascota)
- imagen (archivo)
- fecha_subida (auto_now_add)
```

### **MensajeChat**
```
- id (PK)
- reporte (FK a ReporteMascota)
- usuario (FK a User)
- mensaje (texto)
- fecha (auto_now_add)
```

## 🔌 API Endpoints

### **Obtener Razas**
```
GET /api/razas/
Response: {
    "razas": [
        {"id": 1, "name": "Labrador"},
        ...
    ],
    "fuente": "The Dog API" o "Alternativa"
}
```

### **Chatear**
```
GET /api/chat/mensajes/<reporte_id>/
POST /api/chat/enviar/<reporte_id>/
```

## 📊 Estadísticas en Consola

Cuando cargas el mapa, puedes ver en la consola del navegador (F12):
```
📊 Estadísticas del Mapa:
   🐕 Perros Encontrados: 3
   🔍 Perros Perdidos: 2
   📍 Total de Reportes: 5
```

## 🎨 Frontend - Flujo de Uso

1. **Crear Reporte:**
   - Click en "📍 Reportar Mascota"
   - Click en ubicación en el mapa
   - Se abre formulario modal
   - Selecciona tipo (Encontrado/Perdido)
   - Completa datos
   - Selecciona razas (cargadas desde The Dog API)
   - Adjunta 1-5 imágenes
   - Envía

2. **Ver Reporte:**
   - Click en marcador en el mapa
   - Click en popup
   - Se abre modal con detalles
   - Pestaña "📋 Info": Detalles + imágenes
   - Pestaña "💬 Chat": Conversar

3. **Colores de Marcadores:**
   - Verde (🐕): Perro Encontrado
   - Rojo (🔍): Perro Perdido

## 🔒 Seguridad

- ✅ CSRF tokens en todas las peticiones POST
- ✅ Autenticación requerida para crear reportes y chatear
- ✅ Filtro de contenido obsceno (better-profanity)
- ✅ Validación de archivos (solo imágenes, máximo 5MB)
- ✅ Límite de 5 imágenes por reporte

## 🚀 Dependencias Instaladas

```bash
pip install better-profanity  # Filtrado de contenido
pip install requests          # APIs externas
```

## 📝 Ejemplo de Reporte Completo

```json
{
    "id": 1,
    "titulo": "Perrito café y blanco perdido",
    "descripcion": "Se perdió en el parque el domingo. Es muy amigable.",
    "tipo_reporte": "perdido",
    "tipo_animal": "Perro",
    "color": "Café y blanco",
    "raza_probable": "Cocker Spaniel",
    "tamaño": "mediano",
    "latitud": -33.45,
    "longitud": -70.66,
    "fecha": "04/04/2026 14:30",
    "usuario": "Juan Pérez",
    "imagenes": [
        "/media/mascotas/perrito1.jpg",
        "/media/mascotas/perrito2.jpg"
    ]
}
```

## 🐛 Troubleshooting

**Q: Las razas no se cargan**
- A: Si The Dog API falla, se usan 23 razas alternativas automáticamente

**Q: Las imágenes no se suben**
- A: Verifica que sean menores a 5MB y en formato de imagen

**Q: No puedo chatear**
- A: Necesitas estar autenticado (login requerido)

**Q: ¿Por qué veo dos colores de marcadores?**
- A: Verde = encontrados, Rojo = perdidos. ¡Así distingues rápidamente!

