from django.http import JsonResponse, HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from productos.models import Producto
from .forms import RegistroForm, EdicionUsuarioForm, UsuarioPerfilForm, EmpresaForm, SucursalForm
from .templatetags.tags import control_acceso
from inventario.models import MovimientoInventario, Inventario
from .models import Empresa, Sucursal


@login_required
def inicio(request):
    # Obtener la empresa del usuario logueado
    empresa_usuario = obtener_empresa(request)
    sucursal_usuario = getattr(request.user.perfil, 'sucursal', None)

    # Si el usuario no es supervisor, muestra solo los datos de la sucursal actual
    if sucursal_usuario:
        total_productos = Producto.objects.filter(empresa=empresa_usuario, inventarios__sucursal=sucursal_usuario).distinct().count()
        total_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        productos_bajo_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario, cantidad__lt=F('stock_minimo')).count()
        productos_agotados = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario, cantidad=0).count()
        movimientos_recientes = MovimientoInventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario).order_by('-fecha')[:50]
    else:
        # Si el usuario no tiene sucursal asignada, inicializar variables
        total_productos = 0
        total_stock = 0
        productos_bajo_stock = 0
        productos_agotados = 0
        movimientos_recientes = []

    return render(request, 'inicio.html', {
        'total_productos': total_productos,
        'total_stock': total_stock,
        'productos_bajo_stock': productos_bajo_stock,
        'productos_agotados': productos_agotados,
        'movimientos_recientes': movimientos_recientes,
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


@control_acceso('Administrador')
def empresa_list(request):
    # Obtener todas las empresas
    empresas = Empresa.objects.all()

    # Manejo del formulario para crear/editar una empresa
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            if request.is_ajax():
                data = {
                    'id': empresa.pk,
                    'nombre': empresa.nombre,
                    'direccion': empresa.direccion,
                    'telefono': empresa.telefono,
                    'email': empresa.email
                }
                return JsonResponse(data)
            else:
                return redirect('empresa_list')
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        form = EmpresaForm()

    return render(request, 'empresas.html', {'empresas': empresas, 'form': form})


@control_acceso('Administrador')
def empresa_edit(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            empresa = form.save()
            if request.is_ajax():
                # Devolver solo los datos de la empresa como JSON
                data = {
                    'id': empresa.pk,
                    'nombre': empresa.nombre,
                    'direccion': empresa.direccion,
                    'telefono': empresa.telefono,
                    'email': empresa.email
                }
                return JsonResponse(data)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        if request.is_ajax():
            # Devolver los datos para precargar el formulario
            data = {
                'nombre': empresa.nombre,
                'direccion': empresa.direccion,
                'telefono': empresa.telefono,
                'email': empresa.email
            }
            return JsonResponse(data)


@control_acceso('Administrador')
def empresa_delete(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        return redirect('empresa_list')
    return render(request, 'empresas.html', {'form': EmpresaForm(), 'empresas': Empresa.objects.all()})


@control_acceso('Administrador')
def sucursal_list(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    sucursales = Sucursal.objects.filter(empresa=empresa)

    if request.method == 'POST':
        form = SucursalForm(request.POST)
        if form.is_valid():
            sucursal = form.save(commit=False)
            sucursal.empresa = empresa  # Asignar la empresa antes de guardar
            sucursal.save()

            if request.is_ajax():
                # Si es una solicitud Ajax, devolvemos los datos de la nueva sucursal
                data = {
                    'id': sucursal.id,
                    'nombre': sucursal.nombre,
                    'abreviatura': sucursal.abreviatura,
                    'direccion': sucursal.direccion,
                    'telefono': sucursal.telefono,
                    'empresa': sucursal.empresa.nombre
                }
                return JsonResponse(data)
            else:
                return redirect('sucursal_list', pk=pk)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        form = SucursalForm()

    return render(request, 'sucursales.html', {'sucursales': sucursales, 'empresa': empresa, 'form': form})


@control_acceso('Administrador')
def sucursal_edit(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)

    if request.method == 'POST':
        form = SucursalForm(request.POST, instance=sucursal)
        if form.is_valid():
            sucursal = form.save()
            if request.is_ajax():
                data = {
                    'id': sucursal.pk,
                    'nombre': sucursal.nombre,
                    'abreviatura': sucursal.abreviatura,
                    'direccion': sucursal.direccion,
                    'telefono': sucursal.telefono,
                    'empresa_id': sucursal.empresa_id
                }
                return JsonResponse(data)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        if request.is_ajax():
            data = {
                'nombre': sucursal.nombre,
                'abreviatura': sucursal.abreviatura,
                'direccion': sucursal.direccion,
                'telefono': sucursal.telefono,
                'empresa_id': sucursal.empresa_id
            }
            return JsonResponse(data)


@control_acceso('Administrador')
def sucursal_delete(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)
    if request.method == 'POST':
        sucursal.delete()
        return JsonResponse({'success': True})
    return redirect('sucursal_list')


def obtener_empresa(request: HttpRequest):
    """
    Retorna la empresa asociadas al usuario que hace el request.

    :param request: HttpRequest objeto de Django
    :return: empresa
    """
    usuario_perfil = request.user.perfil  # Accede al perfil del usuario
    empresa = usuario_perfil.empresa  # Obtiene la empresa del perfil

    return empresa


def obtener_sucursal(request: HttpRequest):
    """
    Retorna la sucursal asociadas al usuario que hace el request.

    :param request: HttpRequest objeto de Django
    :return: sucursal
    """
    usuario_perfil = request.user.perfil  # Accede al perfil del usuario
    sucursal = usuario_perfil.sucursal  # Obtiene la sucursal del perfil (puede ser None)

    return sucursal