from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, EdicionUsuarioForm


@login_required
def inicio(request):
    return render(request, 'usuarios/inicio.html')


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('admin')  # Redirige a la página principal
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})

def login_view(request):
    # Si el usuario ya está autenticado, lo redirigimos al inicio
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('inicio')
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})

@login_required
def editar_usuario(request):
    if request.method == 'POST':
        form = EdicionUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('admin')
    else:
        form = EdicionUsuarioForm(instance=request.user)
    return render(request, 'usuarios/editar.html', {'form': form})
