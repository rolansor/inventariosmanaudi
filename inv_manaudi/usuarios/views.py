from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, EdicionUsuarioForm, UsuarioPerfilForm
from django.db.models import F, Sum
from inventario.models import Producto, MovimientoInventario, Inventario


@login_required
def inicio(request):
    # Obtener la empresa del usuario logueado a través de su perfil
    empresa_usuario = request.user.perfil.empresa

    # Filtrar productos y movimientos solo por la empresa del usuario logueado
    total_productos = Producto.objects.filter(empresa=empresa_usuario).count()
    total_stock = Inventario.objects.filter(producto__empresa=empresa_usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    productos_bajo_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, cantidad__lt=F('stock_minimo')).count()
    productos_agotados = Inventario.objects.filter(producto__empresa=empresa_usuario, cantidad=0).count()

    movimientos_recientes = MovimientoInventario.objects.filter(producto__empresa=empresa_usuario).order_by('-fecha')[:10]

    # Productos más movidos solo para la empresa del usuario
    productos_mas_movidos = MovimientoInventario.objects.filter(producto__empresa=empresa_usuario).values('producto__nombre').annotate(
        total=Sum('cantidad')).order_by('-total')[:5]

    return render(request, 'inicio.html', {
        'total_productos': total_productos,
        'total_stock': total_stock,
        'productos_bajo_stock': productos_bajo_stock,
        'productos_agotados': productos_agotados,
        'movimientos_recientes': movimientos_recientes,
        'productos_mas_movidos': productos_mas_movidos,
    })


def logout_view(request):
    logout(request)
    return redirect('login')


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
    return render(request, 'login.html', {'form': form})


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        perfil_form = UsuarioPerfilForm(request.POST)  # Formulario de perfil
        if form.is_valid() and perfil_form.is_valid():
            user = form.save()
            perfil = perfil_form.save(commit=False)
            perfil.usuario = user  # Relacionar el perfil con el usuario
            perfil.save()
            login(request, user)
            return redirect('admin')  # Redirige a la página principal
    else:
        form = RegistroForm()
        perfil_form = UsuarioPerfilForm()  # Formulario de perfil vacío
    return render(request, 'registro.html', {'form': form, 'perfil_form': perfil_form})



@login_required
def editar_usuario(request):
    if request.method == 'POST':
        form = EdicionUsuarioForm(request.POST, instance=request.user)
        perfil_form = UsuarioPerfilForm(request.POST, instance=request.user.perfil)  # Cargar el perfil del usuario
        if form.is_valid() and perfil_form.is_valid():
            form.save()
            perfil_form.save()
            return redirect('admin')
    else:
        form = EdicionUsuarioForm(instance=request.user)
        perfil_form = UsuarioPerfilForm(instance=request.user.perfil)  # Cargar el perfil del usuario
    return render(request, 'editar.html', {'form': form, 'perfil_form': perfil_form})
