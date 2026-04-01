from django.shortcuts import render
from .models import ReporteMascota
import json
from .forms import RegistroPersonalizadoForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from .forms import PerfilUpdateForm # Importamos el nuevo formulario
from django.contrib.auth.decorators import login_required



def mapa(request):
    reportes = ReporteMascota.objects.all()

    data = []
    for r in reportes:
        data.append({
            "titulo": r.titulo,
            "descripcion": r.descripcion,
            "lat": r.latitud,
            "lng": r.longitud,
            "imagen": r.imagen.url if r.imagen else ""
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
        # 1. Atrapamos los datos que vienen del formulario del globo en el mapa
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        imagen = request.FILES.get('imagen') # Usamos FILES porque es una foto

        # 2. Creamos el registro en la base de datos
        ReporteMascota.objects.create(
            # usuario=request.user, # Descomenta esta línea si tu modelo ReporteMascota tiene un campo para enlazar al usuario
            titulo=titulo,
            descripcion=descripcion,
            latitud=lat,   # Aquí usamos los nombres exactos de tu modelo
            longitud=lng,  # Aquí usamos los nombres exactos de tu modelo
            imagen=imagen
        )
        
        # 3. Redirigimos de vuelta al mapa (asegúrate de que tu ruta se llame 'mapa' en urls.py)
        return redirect('mapa') 
        
    return redirect('mapa')
