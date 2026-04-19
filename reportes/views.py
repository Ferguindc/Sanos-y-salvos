from django.shortcuts import render
from .models import ReporteMascota, MensajeChat, ImagenReporte
import json
from .forms import RegistroPersonalizadoForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from .forms import PerfilUpdateForm # Importamos el nuevo formulario
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests
from better_profanity import profanity

# Inicializar profanity
profanity.load_censor_words()



def mapa(request):
    reportes = ReporteMascota.objects.all()

    data = []
    for r in reportes:
        # Obtener la primera imagen del reporte
        primera_imagen = r.imagenes.first()
        imagen_url = primera_imagen.imagen.url if primera_imagen else ""

        data.append({
            "id": r.id,
            "titulo": r.titulo,
            "descripcion": r.descripcion,
            "lat": r.latitud,
            "lng": r.longitud,
            "imagen": imagen_url,
            "tipo_animal": r.tipo_animal,
            "color": r.color,
            "raza_probable": r.raza_probable,
            "tamaño": r.tamaño,
            "tipo_reporte": r.tipo_reporte,  # Enviamos 'encontrado' o 'perdido'
            "fecha": r.fecha.strftime("%d/%m/%Y %H:%M") if r.fecha else "",
            "usuario": r.usuario.first_name or r.usuario.username if r.usuario else "Anónimo"
        })

    return render(request, "mapa.html", {
        "reportes": json.dumps(data)
    })

# 🔐 REGISTRO
def registro(request):
    if request.method == 'POST':
        form = RegistroPersonalizadoForm(request.POST)
        if form.is_valid():
            form.save() # Guarda al usuario en la base de datos
            return redirect('login') # Redirige al login tras registrarse
    else:
        form = RegistroPersonalizadoForm()
    
    return render(request, 'registro.html', {'form': form})

# 🔑 LOGIN
def iniciar_sesion(request):
    if request.method == 'POST':
        # El AuthenticationForm recibe request y los datos del POST
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Si los datos están bien, extraemos usuario y contraseña
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # authenticate verifica en la base de datos si las credenciales coinciden
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user) # ¡Inicia la sesión oficialmente!
                return redirect('index') # Redirigimos a la página principal tras entrar
    else:
        form = AuthenticationForm()
        
    return render(request, 'login.html', {'form': form})

def index(request):
    return render(request, 'index.html')

# 🚪 LOGOUT
# Nueva función para salir de la cuenta
def cerrar_sesion(request):
    logout(request) # Django elimina la sesión de forma segura
    return redirect('index') # Lo devolvemos a la página principal
from django.contrib.auth.decorators import login_required
@login_required
def perfil(request):
    if request.method == 'POST':
        # Le pasamos los nuevos datos y le decimos de quién son (instance=request.user)
        form = PerfilUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('perfil') # Recarga la página para mostrar los cambios
    else:
        # Si solo visita la página, mostramos el formulario con sus datos actuales
        form = PerfilUpdateForm(instance=request.user)
        
    return render(request, 'perfil.html', {'form': form})
@login_required
def crear_reporte(request):
    if request.method == 'POST':
        try:
            # 1. Validar que no sea contenido obsceno
            titulo = request.POST.get('titulo', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            color = request.POST.get('color', '').strip()
            raza = request.POST.get('raza', '').strip()

            if profanity.contains_profanity(titulo) or profanity.contains_profanity(descripcion):
                return JsonResponse({"estado": "error", "mensaje": "El contenido contiene palabras inapropiadas"})

            # 2. Validaciones básicas
            if not titulo or not descripcion:
                return JsonResponse({"estado": "error", "mensaje": "Título y descripción son requeridos"})

            lat = request.POST.get('lat')
            lng = request.POST.get('lng')
            tipo_reporte = request.POST.get('tipo_reporte', 'encontrado')
            tipo_animal = request.POST.get('tipo_animal', '').strip()
            tamaño = request.POST.get('tamaño', '')

            # 3. Crear el reporte
            reporte = ReporteMascota.objects.create(
                usuario=request.user,
                titulo=titulo,
                descripcion=descripcion,
                latitud=float(lat),
                longitud=float(lng),
                tipo_reporte=tipo_reporte,
                tipo_animal=tipo_animal or 'Perro',
                color=color,
                raza_probable=raza,
                tamaño=tamaño
            )

            # 4. Manejar imágenes múltiples (máximo 5)
            imagenes = request.FILES.getlist('imagenes')
            conteo_imagenes = 0

            for imagen in imagenes[:5]:  # Máximo 5 imágenes
                if imagen.size > 5 * 1024 * 1024:  # 5MB máximo por imagen
                    continue
                ImagenReporte.objects.create(reporte=reporte, imagen=imagen)
                conteo_imagenes += 1

            return JsonResponse({
                "estado": "ok",
                "mensaje": f"Reporte creado exitosamente con {conteo_imagenes} imagen(s)",
                "reporte_id": reporte.id
            })

        except Exception as e:
            return JsonResponse({"estado": "error", "mensaje": f"Error: {str(e)}"})

    return JsonResponse({"estado": "error", "mensaje": "Método no permitido"})


# 🐕 API - OBTENER RAZAS DESDE THE DOG API
@require_http_methods(["GET"])
def obtener_razas(request):
    # Lista de razas alternativas por si la API falla
    RAZAS_ALTERNATIVAS = [
        'Labrador', 'Golden Retriever', 'Bulldog', 'Poodle', 'Beagle',
        'Rottweiler', 'Yorkshire Terrier', 'German Shepherd', 'Dachshund',
        'Boxer', 'Chihuahua', 'Siberian Husky', 'Great Dane', 'Shih Tzu',
        'Schnauzer', 'Cocker Spaniel', 'Afghan Hound', 'Irish Setter',
        'Dalmatian', 'Saint Bernard', 'Gryfon', 'Pinscher', 'Viejo Pastor Inglés'
    ]

    try:
        response = requests.get('https://api.thedogapi.com/v1/breeds', timeout=5)
        if response.status_code == 200:
            razas = response.json()
            razas_list = [{'id': r['id'], 'name': r['name']} for r in razas]
            return JsonResponse({"razas": razas_list, "fuente": "The Dog API"})
    except Exception as e:
        print(f"Error conectando con The Dog API: {str(e)}")

    # Si falla la API, usar razas alternativas
    razas_list = [{'id': i, 'name': raza} for i, raza in enumerate(RAZAS_ALTERNATIVAS)]
    return JsonResponse({"razas": razas_list, "fuente": "Alternativa"})


# 💬 CHAT - OBTENER MENSAJES DE UN REPORTE
@login_required
@require_http_methods(["GET"])
def obtener_mensajes(request, reporte_id):
    try:
        reporte = ReporteMascota.objects.get(id=reporte_id)
        mensajes = MensajeChat.objects.filter(reporte=reporte).select_related('usuario')

        data = []
        for m in mensajes:
            data.append({
                "id": m.id,
                "usuario": m.usuario.first_name or m.usuario.username,
                "username": m.usuario.username,
                "mensaje": m.mensaje,
                "fecha": m.fecha.strftime("%H:%M"),
                "es_mi_mensaje": m.usuario.id == request.user.id
            })

        return JsonResponse({"mensajes": data, "estado": "ok"})
    except ReporteMascota.DoesNotExist:
        return JsonResponse({"mensajes": [], "estado": "error", "mensaje": "Reporte no encontrado"}, status=404)


# 💬 CHAT - ENVIAR MENSAJE
@login_required
@require_http_methods(["POST"])
def enviar_mensaje(request, reporte_id):
    if not request.user.is_authenticated:
        return JsonResponse({"estado": "error", "mensaje": "No autenticado"}, status=401)

    try:
        reporte = ReporteMascota.objects.get(id=reporte_id)
        mensaje_text = request.POST.get('mensaje', '').strip()

        if not mensaje_text:
            return JsonResponse({"estado": "error", "mensaje": "El mensaje no puede estar vacío"})

        mensaje = MensajeChat.objects.create(
            reporte=reporte,
            usuario=request.user,
            mensaje=mensaje_text
        )

        return JsonResponse({
            "estado": "ok",
            "mensaje": {
                "id": mensaje.id,
                "usuario": request.user.first_name or request.user.username,
                "username": request.user.username,
                "mensaje": mensaje.mensaje,
                "fecha": mensaje.fecha.strftime("%H:%M"),
                "es_mi_mensaje": True
            }
        })
    except ReporteMascota.DoesNotExist:
        return JsonResponse({"estado": "error", "mensaje": "Reporte no encontrado"}, status=404)


# 🎯 MATCHING DE MASCOTAS - ENDPOINTS
@login_required
@require_http_methods(["GET"])
def obtener_mis_matches(request):
    """
    Obtiene los matches de reportes perdidos del usuario
    Retorna lista de posibles coincidencias entre mascotas perdidas y encontradas
    """
    try:
        # Obtener reportes perdidos del usuario
        mis_reportes_perdidos = ReporteMascota.objects.filter(
            usuario=request.user,
            tipo_reporte='perdido'
        )

        # Obtener matches sin confirmar y sin desmentir
        from .models import PosibleMatch
        matches = PosibleMatch.objects.filter(
            reporte_perdido__in=mis_reportes_perdidos,
            confirmado=False,
            desmentido=False
        ).order_by('-score_similitud').select_related('reporte_encontrado', 'reporte_perdido')

        data = []
        for m in matches:
            # Primera imagen del reporte encontrado
            img_encontrado = m.reporte_encontrado.imagenes.first()
            img_url = img_encontrado.imagen.url if img_encontrado else ""

            data.append({
                'id': m.id,
                'score': f"{m.score_similitud:.0f}",
                'razon': m.razon_match,
                'perdido': {
                    'id': m.reporte_perdido.id,
                    'titulo': m.reporte_perdido.titulo,
                    'tipo_animal': m.reporte_perdido.tipo_animal,
                    'color': m.reporte_perdido.color,
                    'raza': m.reporte_perdido.raza_probable,
                    'tamaño': m.reporte_perdido.tamaño,
                },
                'encontrado': {
                    'id': m.reporte_encontrado.id,
                    'titulo': m.reporte_encontrado.titulo,
                    'tipo_animal': m.reporte_encontrado.tipo_animal,
                    'color': m.reporte_encontrado.color,
                    'raza': m.reporte_encontrado.raza_probable,
                    'tamaño': m.reporte_encontrado.tamaño,
                    'imagen': img_url,
                    'fecha': m.reporte_encontrado.fecha.strftime("%d/%m/%Y %H:%M"),
                    'usuario': m.reporte_encontrado.usuario.first_name or m.reporte_encontrado.usuario.username
                }
            })

        return JsonResponse({'estado': 'ok', 'matches': data})

    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def confirmar_match(request, match_id):
    """
    Usuario confirma que un match es correcto (es su mascota)
    """
    try:
        from .models import PosibleMatch
        from .notifications import enviar_notificacion_confirmacion

        match = PosibleMatch.objects.get(id=match_id)

        # Verificar que el usuario sea el propietario del reporte perdido
        if match.reporte_perdido.usuario != request.user:
            return JsonResponse({'estado': 'error', 'mensaje': 'No autorizado'}, status=403)

        match.confirmado = True
        match.save()

        # Enviar notificación al usuario que reportó como encontrado
        enviar_notificacion_confirmacion(match.id)

        return JsonResponse({
            'estado': 'ok',
            'mensaje': f'Match confirmado. Se notificará al usuario que reportó como encontrado.',
            'match_id': match.id
        })

    except PosibleMatch.DoesNotExist:
        return JsonResponse({'estado': 'error', 'mensaje': 'Match no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def desmentir_match(request, match_id):
    """
    Usuario rechaza un match (no es su mascota)
    """
    try:
        from .models import PosibleMatch

        match = PosibleMatch.objects.get(id=match_id)

        # Verificar que el usuario sea el propietario del reporte perdido
        if match.reporte_perdido.usuario != request.user:
            return JsonResponse({'estado': 'error', 'mensaje': 'No autorizado'}, status=403)

        match.desmentido = True
        match.save()

        return JsonResponse({
            'estado': 'ok',
            'mensaje': 'Match rechazado',
            'match_id': match.id
        })

    except PosibleMatch.DoesNotExist:
        return JsonResponse({'estado': 'error', 'mensaje': 'Match no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': str(e)}, status=500)


@require_http_methods(["POST"])
def ejecutar_matching_manual(request):
    """
    Endpoint para ejecutar matching manualmente (solo para testing)
    """
    if not request.user.is_staff:
        return JsonResponse({'estado': 'error', 'mensaje': 'Solo administradores'}, status=403)

    try:
        from .matching_engine import ejecutar_matching_global
        stats = ejecutar_matching_global()

        return JsonResponse({
            'estado': 'ok',
            'mensaje': 'Matching ejecutado',
            'estadisticas': stats
        })

    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': str(e)}, status=500)

