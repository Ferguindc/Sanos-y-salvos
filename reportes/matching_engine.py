"""
Motor de matching para encontrar posibles coincidencias
entre reportes de mascotas perdidas y encontradas
"""

from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from .models import ReporteMascota, PosibleMatch
from .vision_service import analizar_imagen_openai


RADIO_TIERRA_KM = 6371  # Radio de la tierra en kilómetros


def distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos en la tierra usando la fórmula de Haversine

    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto

    Returns:
        float: Distancia en kilómetros
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return RADIO_TIERRA_KM * c


def extraer_score_imagen(analisis_openai, reporte_ref):
    """
    Calcula score de similitud de imagen usando análisis de OpenAI

    Args:
        analisis_openai (dict): Resultado del análisis de imagen con OpenAI
        reporte_ref (ReporteMascota): Reporte de referencia para comparar

    Returns:
        float: Score de 0-100
    """
    if not analisis_openai.get('exito'):
        return 30  # Confianza baja si el análisis falló

    score = 0

    # Raza (max 40 puntos)
    raza_prob = analisis_openai.get('raza_probable', '').lower()
    raza_ref = reporte_ref.raza_probable.lower() if reporte_ref.raza_probable else ''

    if raza_prob and raza_ref:
        if raza_prob == raza_ref:
            score += 40
        elif raza_prob in raza_ref or raza_ref in raza_prob:
            score += 30
        else:
            score += 5
    elif not raza_ref:
        score += 35  # Si no hay raza de referencia, damos crédito

    # Color (max 30 puntos)
    color_desc = analisis_openai.get('color_descripcion', '').lower()
    color_ref = reporte_ref.color.lower() if reporte_ref.color else ''

    palabras_color_desc = set(color_desc.split())
    palabras_color_ref = set(color_ref.split())

    if palabras_color_desc and palabras_color_ref:
        coincidencias = len(palabras_color_desc & palabras_color_ref)
        similitud = coincidencias / max(len(palabras_color_desc), len(palabras_color_ref))
        score += similitud * 30
    elif color_ref:
        score += 10  # Cierta flexibilidad si no hay descripción de color

    # Tamaño (max 20 puntos)
    tamaño_est = analisis_openai.get('tamaño_estimado', 'mediano').lower()
    tamaño_ref = reporte_ref.tamaño.lower() if reporte_ref.tamaño else ''

    tamaño_map = {
        'pequeño': ['pequeño', 'mini', 'toy', 'chico'],
        'mediano': ['mediano', 'medio'],
        'grande': ['grande', 'gigante']
    }

    for cat, variantes in tamaño_map.items():
        if tamaño_est in variantes and tamaño_ref in variantes:
            score += 20
            break

    # Confianza (max 10 puntos)
    confianza = analisis_openai.get('confianza', 50)
    score += (confianza / 100) * 10

    return min(100, score)


def calcular_score_similitud(reporte_perdido, reporte_encontrado, vision_data=None):
    """
    Calcula un score de similitud entre dos reportes

    Score Components:
    - Similitud de imágenes (OpenAI Vision): 40%
    - Similitud de atributos (raza, color, tamaño): 35%
    - Proximidad geográfica (distancia): 15%
    - Proximidad temporal (fecha): 10%

    Args:
        reporte_perdido (ReporteMascota): Reporte de mascota perdida
        reporte_encontrado (ReporteMascota): Reporte de mascota encontrada
        vision_data (dict): Datos de análisis previo de visión (opcional)

    Returns:
        float: Score de similitud (0-100)
    """

    score_componentes = {
        'imagen': 0,
        'atributos': 0,
        'ubicacion': 0,
        'fecha': 0
    }

    # ====================
    # 1. SIMILITUD DE IMAGEN (40%)
    # ====================
    # Si no tenemos datos de visión, analizamos la primera imagen
    if not vision_data:
        try:
            imagen_encontrada = reporte_encontrado.imagenes.first()
            if imagen_encontrada and imagen_encontrada.imagen:
                vision_data = analizar_imagen_openai(imagen_encontrada.imagen.path)
            else:
                vision_data = {'exito': False}
        except:
            vision_data = {'exito': False}

    score_imagen = extraer_score_imagen(vision_data, reporte_perdido)
    score_componentes['imagen'] = score_imagen * 0.40

    # ====================
    # 2. SIMILITUD DE ATRIBUTOS (35%)
    # ====================
    score_atributos = 0

    # Tipo animal
    if reporte_perdido.tipo_animal.lower() == reporte_encontrado.tipo_animal.lower():
        score_atributos += 10
    else:
        score_atributos += 0

    # Raza (10 puntos)
    raza_perd = reporte_perdido.raza_probable.lower().strip() if reporte_perdido.raza_probable else ''
    raza_encon = reporte_encontrado.raza_probable.lower().strip() if reporte_encontrado.raza_probable else ''

    if raza_perd and raza_encon:
        if raza_perd == raza_encon:
            score_atributos += 10
        elif raza_perd in raza_encon or raza_encon in raza_perd:
            score_atributos += 6
    elif not raza_perd and not raza_encon:
        score_atributos += 3  # Ambos sin raza especificada

    # Color (10 puntos)
    color_perd = reporte_perdido.color.lower() if reporte_perdido.color else ''
    color_encon = reporte_encontrado.color.lower() if reporte_encontrado.color else ''

    palabras_perd = set(color_perd.split())
    palabras_encon = set(color_encon.split())

    if palabras_perd and palabras_encon:
        coincidencias = len(palabras_perd & palabras_encon)
        similitud_color = coincidencias / max(len(palabras_perd), len(palabras_encon))
        score_atributos += similitud_color * 10
    elif not color_perd or not color_encon:
        score_atributos += 2

    # Tamaño (5 puntos)
    tam_perd = reporte_perdido.tamaño if reporte_perdido.tamaño else ''
    tam_encon = reporte_encontrado.tamaño if reporte_encontrado.tamaño else ''

    if tam_perd and tam_encon:
        if tam_perd == tam_encon:
            score_atributos += 5

    score_componentes['atributos'] = min(35, score_atributos)

    # ====================
    # 3. PROXIMIDAD GEOGRÁFICA (15%)
    # ====================
    distancia_km = distancia_haversine(
        reporte_perdido.latitud,
        reporte_perdido.longitud,
        reporte_encontrado.latitud,
        reporte_encontrado.longitud
    )

    # Máximo 10km de tolerancia
    if distancia_km <= 0.5:
        score_ubicacion = 15  # Mismo lugar
    elif distancia_km <= 2:
        score_ubicacion = 12
    elif distancia_km <= 5:
        score_ubicacion = 8
    elif distancia_km <= 10:
        score_ubicacion = 4
    else:
        score_ubicacion = 0

    score_componentes['ubicacion'] = score_ubicacion

    # ====================
    # 4. PROXIMIDAD TEMPORAL (10%)
    # ====================
    dias_diferencia = abs((reporte_perdido.fecha - reporte_encontrado.fecha).days)

    if dias_diferencia == 0:
        score_fecha = 10
    elif dias_diferencia <= 1:
        score_fecha = 9
    elif dias_diferencia <= 3:
        score_fecha = 7
    elif dias_diferencia <= 7:
        score_fecha = 4
    elif dias_diferencia <= 30:
        score_fecha = 1
    else:
        score_fecha = 0

    score_componentes['fecha'] = score_fecha

    # ====================
    # PUNTUACIÓN FINAL
    # ====================
    score_total = sum(score_componentes.values())

    return {
        'score_total': min(100, score_total),
        'detalles': score_componentes,
        'distancia_km': distancia_km,
        'dias_diferencia': dias_diferencia
    }


def generar_razon_match(reporte_perdido, reporte_encontrado, score_data):
    """
    Genera una explicación legible del match

    Args:
        reporte_perdido (ReporteMascota): Reporte de mascota perdida
        reporte_encontrado (ReporteMascota): Reporte de mascota encontrada
        score_data (dict): Datos del scoring

    Returns:
        str: Explicación del match
    """
    razones = []

    detalles = score_data.get('detalles', {})
    distancia = score_data.get('distancia_km', 0)
    dias = score_data.get('dias_diferencia', 0)

    if detalles.get('imagen', 0) > 25:
        razones.append("Similitud de apariencia (imagen)")

    if detalles.get('atributos', 0) > 20:
        razones.append("Características coincidentes (raza, color, tamaño)")

    if distancia <= 5:
        razones.append(f"Ubicación cercana ({distancia:.1f} km)")

    if dias <= 7:
        razones.append(f"Reportes recientes (con {dias} días de diferencia)")

    razon_final = "Posible match por: " + ", ".join(razones) if razones else "Similitud general entre reportes"

    return razon_final


def buscar_matches_para_reporte(reporte_id):
    """
    Ejecuta el matching para un reporte específico

    Args:
        reporte_id (int): ID del reporte

    Returns:
        list: Lista de matches creados
    """
    try:
        reporte = ReporteMascota.objects.get(id=reporte_id)
    except ReporteMascota.DoesNotExist:
        return []

    matches_creados = []

    # Si es un reporte perdido, buscar reportes encontrados
    if reporte.tipo_reporte == 'perdido':
        reportes_candidatos = ReporteMascota.objects.filter(
            tipo_reporte='encontrado',
            tipo_animal=reporte.tipo_animal,
            fecha__gte=timezone.now() - timedelta(days=30)
        ).exclude(id=reporte.id)

        for candidato in reportes_candidatos:
            # Evitar duplicados
            if PosibleMatch.objects.filter(
                Q(reporte_perdido=reporte, reporte_encontrado=candidato) |
                Q(reporte_perdido=candidato, reporte_encontrado=reporte)
            ).exists():
                continue

            score_data = calcular_score_similitud(reporte, candidato)

            if score_data['score_total'] >= 50:  # Umbral mínimo
                razon = generar_razon_match(reporte, candidato, score_data)

                try:
                    match = PosibleMatch.objects.create(
                        reporte_perdido=reporte,
                        reporte_encontrado=candidato,
                        score_similitud=score_data['score_total'],
                        razon_match=razon
                    )
                    matches_creados.append(match)
                except Exception as e:
                    print(f"Error creando match: {str(e)}")

    # Si es un reporte encontrado, buscar reportes perdidos
    elif reporte.tipo_reporte == 'encontrado':
        reportes_candidatos = ReporteMascota.objects.filter(
            tipo_reporte='perdido',
            tipo_animal=reporte.tipo_animal,
            fecha__gte=timezone.now() - timedelta(days=30)
        ).exclude(id=reporte.id)

        for candidato in reportes_candidatos:
            # Evitar duplicados
            if PosibleMatch.objects.filter(
                Q(reporte_perdido=candidato, reporte_encontrado=reporte) |
                Q(reporte_perdido=reporte, reporte_encontrado=candidato)
            ).exists():
                continue

            score_data = calcular_score_similitud(candidato, reporte)

            if score_data['score_total'] >= 50:  # Umbral mínimo
                razon = generar_razon_match(candidato, reporte, score_data)

                try:
                    match = PosibleMatch.objects.create(
                        reporte_perdido=candidato,
                        reporte_encontrado=reporte,
                        score_similitud=score_data['score_total'],
                        razon_match=razon
                    )
                    matches_creados.append(match)
                except Exception as e:
                    print(f"Error creando match: {str(e)}")

    return matches_creados


def ejecutar_matching_global():
    """
    Ejecuta matching para TODOS los reportes
    (usualmente ejecutado por tareas en background)

    Returns:
        dict: Estadísticas de ejecución
    """
    stats = {
        'reportes_procesados': 0,
        'matches_creados': 0,
        'matches_notificados': 0
    }

    # Reportes perdidos de últimos 30 días
    reportes_perdidos = ReporteMascota.objects.filter(
        tipo_reporte='perdido',
        fecha__gte=timezone.now() - timedelta(days=30)
    )

    for reporte_perdido in reportes_perdidos:
        matches = buscar_matches_para_reporte(reporte_perdido.id)
        stats['reportes_procesados'] += 1
        stats['matches_creados'] += len(matches)

    return stats
