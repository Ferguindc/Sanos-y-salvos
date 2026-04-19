"""
Servicio de visión por computadora usando OpenAI Vision API
para analizar imágenes de mascotas
"""

import base64
import json
import os
from django.conf import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def analizar_imagen_openai(image_path):
    """
    Analiza una imagen de mascota usando OpenAI Vision API

    Args:
        image_path (str): Ruta al archivo de imagen

    Returns:
        dict: Análisis de la imagen con:
            - raza_probable: Raza probable del animal
            - coloresdescripcion: Descripción de colores
            - tamaño_estimado: Tamaño (pequeño/mediano/grande)
            - caracteristicas: Lista de características distintivas
            - confianza: Nivel de confianza (0-100)
    """

    if not os.path.exists(image_path):
        return {
            'error': 'Archivo no encontrado',
            'raza_probable': '',
            'color_descripcion': '',
            'tamaño_estimado': '',
            'caracteristicas': [],
            'confianza': 0
        }

    try:
        # Leer imagen y convertir a base64
        with open(image_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode()

        # Obtener extensión del archivo
        ext = os.path.splitext(image_path)[1].lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(ext, 'image/jpeg')

        # Enviar a OpenAI Vision
        prompt = """
        Analiza esta imagen de mascota. Proporciona la información en formato JSON.

        {
            "raza_probable": "La raza más probable del animal",
            "color_descripcion": "Descripción detallada de los colores (ej: 'marrón y blanco')",
            "tamaño_estimado": "pequeño, mediano o grande",
            "caracteristicas": ["lista", "de", "características", "distintivas"],
            "confianza": 85
        }

        Sé específico y detallado. Incluye características como:
        - Tipo de pelaje (largo, corto, rizado, etc.)
        - Forma de orejas
        - Marca o manchas especiales
        - Largo estimado de cola
        - Cualquier cicatriz o marca distintiva

        Confianza: 0-100, donde 100 es completamente seguro de que es un perro y 50 es incierto.
        """

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
            max_tokens=500,
        )

        # Extraer respuesta JSON
        respuesta_texto = response.choices[0].message.content

        # Intentar parsear JSON
        try:
            # Buscar JSON en la respuesta
            json_inicio = respuesta_texto.find('{')
            json_fin = respuesta_texto.rfind('}') + 1

            if json_inicio != -1 and json_fin > json_inicio:
                json_str = respuesta_texto[json_inicio:json_fin]
                resultado = json.loads(json_str)

                # Validar campos
                return {
                    'raza_probable': resultado.get('raza_probable', ''),
                    'color_descripcion': resultado.get('color_descripcion', ''),
                    'tamaño_estimado': resultado.get('tamaño_estimado', 'mediano'),
                    'caracteristicas': resultado.get('caracteristicas', []),
                    'confianza': resultado.get('confianza', 50),
                    'exito': True
                }
        except json.JSONDecodeError:
            pass

        # Si no se pudo parsear JSON, devolver estructura genérica
        return {
            'raza_probable': 'No especificada',
            'color_descripcion': respuesta_texto[:100],
            'tamaño_estimado': 'mediano',
            'caracteristicas': [respuesta_texto[:50]],
            'confianza': 30,
            'exito': False
        }

    except Exception as e:
        print(f"Error analizando imagen con OpenAI Vision: {str(e)}")
        return {
            'error': str(e),
            'raza_probable': '',
            'color_descripcion': '',
            'tamaño_estimado': '',
            'caracteristicas': [],
            'confianza': 0,
            'exito': False
        }


def extraer_raza_de_descripcion(color_desc):
    """
    Intenta extraer información de raza del texto de descripción
    para casos donde la análisis no fue perfecto

    Args:
        color_desc (str): Descripción de color/características

    Returns:
        str: Palabra clave que podría indicar una raza
    """
    keywords_raza = {
        'labrador': ['labrador', 'lab'],
        'cocker': ['cocker', 'spaniel'],
        'bulldog': ['bulldog'],
        'poodle': ['poodle', 'caniche'],
        'beagle': ['beagle'],
        'pastor alemán': ['pastor', 'alemán', 'pastor alemán'],
        'husky': ['husky', 'siberiano'],
        'chihuahua': ['chihuahua', 'mini'],
        'golden': ['golden', 'retriever'],
    }

    desc_lower = color_desc.lower()
    for raza, palabras_clave in keywords_raza.items():
        for palabra in palabras_clave:
            if palabra in desc_lower:
                return raza

    return ''
