from django.http import JsonResponse, HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from productos.models import Producto
from .forms import EmpresaForm, SucursalForm
from .templatetags.tags import control_acceso
from inventario.models import MovimientoInventario, Inventario
from .models import Empresa, Sucursal


@login_required
def inicio(request):
    # Obtener la empresa del usuario logueado
    empresa_usuario = obtener_empresa(request)
    sucursal_usuario = getattr(request.user.perfil, 'sucursal', None) if hasattr(request.user, 'perfil') else None

    # Si el usuario tiene sucursal específica, muestra solo los datos de su sucursal
    if sucursal_usuario:
        total_productos = Producto.objects.filter(empresa=empresa_usuario, inventarios__sucursal=sucursal_usuario).distinct().count()
        total_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        productos_bajo_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario, cantidad__lt=F('stock_minimo')).count()
        productos_agotados = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario, cantidad=0).count()
        movimientos_recientes = MovimientoInventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario).order_by('-fecha')
    else:
        # Si el usuario no tiene sucursal (admin/supervisor), mostrar datos de toda la empresa
        if empresa_usuario:
            total_productos = Producto.objects.filter(empresa=empresa_usuario).distinct().count()
            total_stock = Inventario.objects.filter(producto__empresa=empresa_usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
            productos_bajo_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, cantidad__lt=F('stock_minimo')).count()
            productos_agotados = Inventario.objects.filter(producto__empresa=empresa_usuario, cantidad=0).count()
            movimientos_recientes = MovimientoInventario.objects.filter(producto__empresa=empresa_usuario).order_by('-fecha')
        else:
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
        'empresa_actual': empresa_usuario,
        'sucursal_actual': sucursal_usuario,
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


@control_acceso('Manaudi')
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


@control_acceso('Manaudi')
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


@control_acceso('Manaudi')
def empresa_delete(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        return redirect('empresa_list')
    return render(request, 'empresas.html', {'form': EmpresaForm(), 'empresas': Empresa.objects.all()})


@control_acceso('Manaudi')
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


@control_acceso('Manaudi')
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


@control_acceso('Manaudi')
def sucursal_delete(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)
    if request.method == 'POST':
        sucursal.delete()
        return JsonResponse({'success': True})
    return redirect('sucursal_list')


def obtener_empresa(request: HttpRequest):
    """
    Retorna la empresa asociadas al usuario que hace el request.
    Para superadmins, permite cambiar entre empresas usando la sesión.

    :param request: HttpRequest objeto de Django
    :return: empresa
    """
    # Si es superadmin, puede ver cualquier empresa
    if request.user.is_superuser:
        # Buscar empresa en sesión
        empresa_id = request.session.get('empresa_id')
        if empresa_id:
            try:
                return Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                pass
        
        # Si no hay empresa en sesión, usar la primera disponible
        primera_empresa = Empresa.objects.first()
        if primera_empresa:
            request.session['empresa_id'] = primera_empresa.id
            return primera_empresa
        return None
    
    # Usuario normal - usar su empresa asignada
    if hasattr(request.user, 'perfil'):
        usuario_perfil = request.user.perfil  # Accede al perfil del usuario
        empresa = usuario_perfil.empresa  # Obtiene la empresa del perfil
        return empresa
    
    return None


def obtener_sucursal(request: HttpRequest):
    """
    Retorna la sucursal asociadas al usuario que hace el request.

    :param request: HttpRequest objeto de Django
    :return: sucursal
    """
    usuario_perfil = request.user.perfil  # Accede al perfil del usuario
    sucursal = usuario_perfil.sucursal  # Obtiene la sucursal del perfil (puede ser None)

    return sucursal


@login_required
def cambiar_empresa(request, empresa_id):
    """
    Permite a los superadmins cambiar la empresa activa en la sesión.
    
    :param request: HttpRequest objeto de Django
    :param empresa_id: ID de la empresa a seleccionar
    :return: redirect a la página anterior o inicio
    """
    if request.user.is_superuser:
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            request.session['empresa_id'] = empresa.id
        except Empresa.DoesNotExist:
            from django.contrib import messages
            messages.error(request, 'Empresa no encontrada')
    
    # Redirigir a la página anterior o al inicio
    return redirect(request.META.get('HTTP_REFERER', 'inicio'))