"""
Vistas de la app ``usuarios``: autenticación, dashboard y administración de
empresas y sucursales (rol Manaudi).

También define ``obtener_empresa``, el helper que todas las demás apps usan para
saber sobre qué empresa está trabajando el usuario.
"""
from django.contrib import messages
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from productos.models import Producto
from .forms import EmpresaForm, SucursalForm
from .templatetags.tags import control_acceso
from .utils import es_ajax
from inventario.models import MovimientoInventario, Inventario
from .models import Empresa, Sucursal


# ---------------------------------------------------------------------------
# Helpers de contexto (empresa activa)
# ---------------------------------------------------------------------------

def obtener_empresa(request: HttpRequest):
    """
    Devuelve la empresa sobre la que trabaja el usuario de la petición.

    - **Superusuario**: usa la empresa guardada en ``request.session['empresa_id']``
      (se cambia desde el selector de la barra superior, vista ``cambiar_empresa``).
      Si no hay ninguna en sesión, toma la primera empresa y la deja en sesión.
    - **Usuario normal**: la empresa de su ``UsuarioPerfil``.
    - Sin perfil ni empresas: ``None`` (el dashboard muestra ceros).

    Todas las vistas de negocio filtran sus consultas por este valor; es la pieza
    central del aislamiento multi-empresa.
    """
    if request.user.is_superuser:
        empresa_id = request.session.get('empresa_id')
        if empresa_id:
            try:
                return Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                pass

        primera_empresa = Empresa.objects.first()
        if primera_empresa:
            request.session['empresa_id'] = primera_empresa.id
            return primera_empresa
        return None

    if hasattr(request.user, 'perfil'):
        return request.user.perfil.empresa

    return None


# ---------------------------------------------------------------------------
# Autenticación y dashboard
# ---------------------------------------------------------------------------

@login_required
def inicio(request):
    """
    Dashboard (``/``): tarjetas de resumen y últimos 10 movimientos.

    Si el usuario tiene sucursal asignada, las cifras son solo de esa sucursal; si no
    (Manaudi, Auditor, superusuario) son de toda la empresa activa.
    """
    empresa_usuario = obtener_empresa(request)
    sucursal_usuario = getattr(request.user.perfil, 'sucursal', None) if hasattr(request.user, 'perfil') else None

    if sucursal_usuario:
        total_productos = Producto.objects.filter(empresa=empresa_usuario, inventarios__sucursal=sucursal_usuario).distinct().count()
        total_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        productos_bajo_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario, cantidad__lt=F('stock_minimo')).count()
        productos_agotados = Inventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario, cantidad=0).count()
        movimientos_recientes = MovimientoInventario.objects.filter(producto__empresa=empresa_usuario, sucursal=sucursal_usuario)
    elif empresa_usuario:
        total_productos = Producto.objects.filter(empresa=empresa_usuario).distinct().count()
        total_stock = Inventario.objects.filter(producto__empresa=empresa_usuario).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        productos_bajo_stock = Inventario.objects.filter(producto__empresa=empresa_usuario, cantidad__lt=F('stock_minimo')).count()
        productos_agotados = Inventario.objects.filter(producto__empresa=empresa_usuario, cantidad=0).count()
        movimientos_recientes = MovimientoInventario.objects.filter(producto__empresa=empresa_usuario)
    else:
        total_productos = 0
        total_stock = 0
        productos_bajo_stock = 0
        productos_agotados = 0
        movimientos_recientes = MovimientoInventario.objects.none()

    movimientos_recientes = (movimientos_recientes
                             .select_related('producto', 'usuario')
                             .order_by('-fecha')[:10])

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
    """Cierra la sesión y vuelve al login."""
    logout(request)
    return redirect('login')


def login_view(request):
    """
    Pantalla de ingreso (usuario y contraseña con ``AuthenticationForm``).

    Un usuario ya autenticado es enviado directamente al dashboard. La casilla
    "Recuérdame" de la plantilla es solo visual: no cambia la duración de la sesión.
    """
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


@login_required
def cambiar_empresa(request, empresa_id):
    """
    Cambia la empresa activa en sesión. Solo tiene efecto para superusuarios.

    Se invoca desde el selector de empresa de la barra superior y vuelve a la página
    desde la que se llamó (``HTTP_REFERER``) o al inicio.
    """
    if request.user.is_superuser:
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            request.session['empresa_id'] = empresa.id
        except Empresa.DoesNotExist:
            messages.error(request, 'Empresa no encontrada')

    return redirect(request.META.get('HTTP_REFERER', 'inicio'))


# ---------------------------------------------------------------------------
# Empresas (rol Manaudi). La pantalla es un listado con formulario AJAX.
# ---------------------------------------------------------------------------

def _empresa_a_json(empresa):
    """Representación JSON de una empresa para las respuestas AJAX del listado."""
    return {
        'id': empresa.pk,
        'nombre': empresa.nombre,
        'direccion': empresa.direccion,
        'telefono': empresa.telefono,
        'email': empresa.email,
    }


@control_acceso('Manaudi')
def empresa_list(request):
    """
    Lista todas las empresas y crea una nueva (POST).

    Por AJAX devuelve la empresa creada en JSON para insertarla en la tabla sin
    recargar; por POST normal redirige al mismo listado.
    """
    empresas = Empresa.objects.all()

    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            if es_ajax(request):
                return JsonResponse(_empresa_a_json(empresa))
            return redirect('empresa_list')
        return JsonResponse({'error': 'Formulario no válido', 'errors': form.errors}, status=400)

    form = EmpresaForm()
    return render(request, 'empresas.html', {'empresas': empresas, 'form': form})


@control_acceso('Manaudi')
def empresa_edit(request, pk):
    """
    Edita una empresa.

    - GET por AJAX: devuelve los datos actuales para precargar el formulario.
    - POST: guarda los cambios y devuelve la empresa en JSON (o redirige si no es AJAX).
    - GET directo en el navegador: vuelve al listado.
    """
    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            empresa = form.save()
            if es_ajax(request):
                return JsonResponse(_empresa_a_json(empresa))
            return redirect('empresa_list')
        return JsonResponse({'error': 'Formulario no válido', 'errors': form.errors}, status=400)

    if es_ajax(request):
        return JsonResponse(_empresa_a_json(empresa))
    return redirect('empresa_list')


@control_acceso('Manaudi')
def empresa_delete(request, pk):
    """
    Elimina una empresa (solo POST). Borra en cascada sucursales, perfiles,
    categorías, productos, inventarios y movimientos de esa empresa.
    """
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        return redirect('empresa_list')
    return render(request, 'empresas.html', {'form': EmpresaForm(), 'empresas': Empresa.objects.all()})


# ---------------------------------------------------------------------------
# Sucursales (rol Manaudi). Igual que empresas: listado + formulario AJAX.
# ---------------------------------------------------------------------------

def _sucursal_a_json(sucursal):
    """Representación JSON de una sucursal para las respuestas AJAX del listado."""
    return {
        'id': sucursal.pk,
        'nombre': sucursal.nombre,
        'abreviatura': sucursal.abreviatura,
        'tipo_sucursal': sucursal.tipo_sucursal,
        'tipo_sucursal_display': sucursal.get_tipo_sucursal_display(),
        'direccion': sucursal.direccion,
        'telefono': sucursal.telefono,
        'empresa': sucursal.empresa.nombre,
        'empresa_id': sucursal.empresa_id,
    }


@control_acceso('Manaudi')
def sucursal_list(request, pk):
    """
    Lista las sucursales de la empresa ``pk`` y crea una nueva (POST).

    La empresa de la nueva sucursal se toma de la URL, no del formulario.
    """
    empresa = get_object_or_404(Empresa, pk=pk)
    sucursales = Sucursal.objects.filter(empresa=empresa)

    if request.method == 'POST':
        form = SucursalForm(request.POST)
        if form.is_valid():
            sucursal = form.save(commit=False)
            sucursal.empresa = empresa
            sucursal.save()
            if es_ajax(request):
                return JsonResponse(_sucursal_a_json(sucursal))
            return redirect('sucursal_list', pk=pk)
        return JsonResponse({'error': 'Formulario no válido', 'errors': form.errors}, status=400)

    form = SucursalForm()
    return render(request, 'sucursales.html', {'sucursales': sucursales, 'empresa': empresa, 'form': form})


@control_acceso('Manaudi')
def sucursal_edit(request, pk):
    """
    Edita una sucursal. Mismo contrato que ``empresa_edit``: GET AJAX precarga,
    POST guarda, GET directo vuelve al listado de la empresa.
    """
    sucursal = get_object_or_404(Sucursal, pk=pk)

    if request.method == 'POST':
        form = SucursalForm(request.POST, instance=sucursal)
        if form.is_valid():
            sucursal = form.save()
            if es_ajax(request):
                return JsonResponse(_sucursal_a_json(sucursal))
            return redirect('sucursal_list', pk=sucursal.empresa_id)
        return JsonResponse({'error': 'Formulario no válido', 'errors': form.errors}, status=400)

    if es_ajax(request):
        return JsonResponse(_sucursal_a_json(sucursal))
    return redirect('sucursal_list', pk=sucursal.empresa_id)


@control_acceso('Manaudi')
def sucursal_delete(request, pk):
    """
    Elimina una sucursal (solo POST). Borra en cascada su inventario, sus movimientos
    y los perfiles de usuario asignados a ella.
    """
    sucursal = get_object_or_404(Sucursal, pk=pk)
    if request.method == 'POST':
        empresa_id = sucursal.empresa_id
        sucursal.delete()
        if es_ajax(request):
            return JsonResponse({'success': True})
        return redirect('sucursal_list', pk=empresa_id)
    return redirect('sucursal_list', pk=sucursal.empresa_id)
