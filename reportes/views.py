from django.shortcuts import render
from .models import ReporteMascota
import json

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect


# Create your views here.




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
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('mapa')
    else:
        form = UserCreationForm()

    return render(request, 'registro.html', {'form': form})


# 🔑 LOGIN
def iniciar_sesion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('mapa')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


# 🚪 LOGOUT
def cerrar_sesion(request):
    logout(request)
    return redirect('mapa')