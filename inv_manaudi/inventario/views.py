"""
Vistas de la app ``inventario``.

Operación (grupo **Encargado**):

- ``movimiento_inventario`` → ``/inventario/movimiento_inventario/`` (entradas y salidas)
- ``iniciar_traslado``      → ``/inventario/traslado/iniciar/``
- ``traslados_pendientes``  → ``/inventario/traslados_pendientes/`` ("Acuse Recibo")
- ``confirmar_traslado``    → ``/inventario/traslado/confirmar/<pk>/``
- ``movimientos_por_producto`` → ``/inventario/producto_movimientos/``

Consulta ampliada (grupo **Supervisor**):

- ``movimientos_por_empresa``  → ``/inventario/empresa_movimientos/``
- ``movimientos_por_sucursal`` → ``/inventario/sucursal_movimientos/``

Todas filtran por la empresa activa (``obtener_empresa``). La lógica de stock vive en
los modelos (``MovimientoInventario.save``, ``Traslado.save`` y ``Traslado.confirmar``);
las vistas solo capturan el ``ValueError`` que estos lanzan y lo muestran al usuario.
"""
from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from usuarios.views import obtener_empresa
from usuarios.templatetags.tags import control_acceso
from .models import MovimientoInventario, Traslado
from .forms import MovimientoInventarioForm, ProductoSelectForm, SucursalSelectForm, TrasladoForm, \
    ConfirmarRecepcionForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sucursal_del_usuario(request):
    """Sucursal asignada al usuario, o None si no tiene perfil o no tiene sucursal."""
    perfil = getattr(request.user, 'perfil', None)
    return perfil.sucursal if perfil else None


def _puede_confirmar(sucursal_usuario, traslado):
    """
    Un usuario con sucursal asignada solo confirma traslados destinados a su sucursal.
    Un usuario sin sucursal (Manaudi, supervisores generales, superusuario) puede
    confirmar cualquier traslado de su empresa.
    """
    return sucursal_usuario is None or traslado.sucursal_destino_id == sucursal_usuario.id


# ---------------------------------------------------------------------------
# Entradas y salidas
# ---------------------------------------------------------------------------

@control_acceso('Encargado')
def movimiento_inventario(request):
    """
    Registra una entrada o salida de stock y muestra los últimos 20 movimientos de
    la empresa.

    El stock se actualiza en ``MovimientoInventario.save()``; si una salida supera el
    saldo, el ``ValueError`` se muestra como error general del formulario.
    """
    empresa_actual = obtener_empresa(request)
    sucursal_usuario = _sucursal_del_usuario(request)

    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST, request.FILES,
                                        empresa=empresa_actual, sucursal=sucursal_usuario)
        if form.is_valid():
            try:
                movimiento = form.save(commit=False)
                movimiento.usuario = request.user
                movimiento.save()
                messages.success(request, 'Movimiento registrado exitosamente.')
                return redirect('movimiento_inventario')
            except ValueError as e:
                form.add_error(None, str(e))
        else:
            messages.error(request, 'Por favor, corrige los errores indicados.')
    else:
        form = MovimientoInventarioForm(empresa=empresa_actual, sucursal=sucursal_usuario)

    movimientos = (MovimientoInventario.objects
                   .filter(producto__empresa=empresa_actual)
                   .select_related('producto', 'sucursal')
                   .order_by('-fecha')[:20])

    return render(request, 'movimiento_inventario.html', {
        'form': form,
        'movimientos': movimientos,
    })


# ---------------------------------------------------------------------------
# Traslados
# ---------------------------------------------------------------------------

@control_acceso('Encargado')
def iniciar_traslado(request):
    """
    Inicia un traslado entre dos sucursales de la empresa activa.

    Al guardar, ``Traslado.save()`` descuenta el stock en origen (movimiento de
    salida) y deja el traslado ``pendiente``. Muestra además los 10 últimos traslados.
    """
    empresa_actual = obtener_empresa(request)

    if request.method == 'POST':
        form = TrasladoForm(request.POST, request.FILES, empresa=empresa_actual)
        if form.is_valid():
            traslado = form.save(commit=False)
            traslado.usuario = request.user
            try:
                traslado.save()
                messages.success(request, 'Traslado iniciado exitosamente.')
                return redirect('traslados_pendientes')
            except ValueError as e:
                form.add_error(None, str(e))
        else:
            messages.error(request, 'Por favor, corrige los errores indicados.')
    else:
        form = TrasladoForm(empresa=empresa_actual)

    traslados_recientes = (Traslado.objects
                           .filter(producto__empresa=empresa_actual)
                           .select_related('producto', 'sucursal_origen', 'sucursal_destino', 'usuario')
                           .order_by('-fecha_creacion')[:10])

    return render(request, 'iniciar_traslado.html', {
        'form': form,
        'traslados_recientes': traslados_recientes,
    })


@control_acceso('Encargado')
def traslados_pendientes(request):
    """
    Lista los traslados pendientes de confirmar ("Acuse Recibo").

    Un usuario del grupo Supervisor o sin sucursal ve todos los pendientes de la
    empresa; el resto solo los destinados a su sucursal. El botón "Confirmar" se
    muestra solo para los que el usuario puede confirmar (ver ``_puede_confirmar``).
    """
    empresa_actual = obtener_empresa(request)
    sucursal_usuario = _sucursal_del_usuario(request)

    pendientes = Traslado.objects.filter(
        producto__empresa=empresa_actual, estado='pendiente'
    ).select_related('producto', 'sucursal_origen', 'sucursal_destino').order_by('-fecha_creacion')

    es_supervisor = request.user.groups.filter(name="Supervisor").exists()
    if sucursal_usuario is not None and not es_supervisor:
        pendientes = pendientes.filter(sucursal_destino=sucursal_usuario)

    return render(request, 'traslados_pendientes.html', {
        'movimientos_pendientes': pendientes,
        'sucursal_usuario': sucursal_usuario,
    })


@control_acceso('Encargado')
def confirmar_traslado(request, pk):
    """
    Confirma la recepción de un traslado pendiente indicando la cantidad recibida.

    ``Traslado.confirmar()`` crea el movimiento de entrada en destino y cambia el
    estado a ``confirmado``. Si el usuario no puede confirmar ese traslado se le
    devuelve al listado con un mensaje de error.
    """
    empresa_actual = obtener_empresa(request)
    traslado = get_object_or_404(Traslado, pk=pk, estado='pendiente', producto__empresa=empresa_actual)
    sucursal_usuario = _sucursal_del_usuario(request)
    if not _puede_confirmar(sucursal_usuario, traslado):
        messages.error(request, 'No tienes permiso para confirmar este traslado.')
        return redirect('traslados_pendientes')

    if request.method == 'POST':
        form = ConfirmarRecepcionForm(request.POST, instance=traslado)
        if form.is_valid():
            try:
                traslado.confirmar()
                messages.success(request, 'Recepción confirmada exitosamente.')
                return redirect('traslados_pendientes')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = ConfirmarRecepcionForm(instance=traslado)

    return render(request, 'confirmar_traslado.html', {
        'form': form,
        'movimiento': traslado,
    })


# ---------------------------------------------------------------------------
# Consultas de movimientos
# ---------------------------------------------------------------------------

@control_acceso('Supervisor')
def movimientos_por_empresa(request):
    """Historial completo de movimientos y traslados de la empresa activa (dos tablas)."""
    empresa_actual = obtener_empresa(request)

    movimientos = MovimientoInventario.objects.filter(
        producto__empresa=empresa_actual
    ).select_related('producto', 'sucursal', 'usuario').order_by('-fecha')

    traslados = Traslado.objects.filter(
        producto__empresa=empresa_actual
    ).select_related('producto', 'sucursal_origen', 'sucursal_destino', 'usuario').order_by('-fecha_creacion')

    return render(request, 'movimientos_por_empresa.html', {
        'movimientos': movimientos,
        'traslados': traslados,
        'empresa': empresa_actual,
    })


@control_acceso('Supervisor')
def movimientos_por_sucursal(request):
    """
    Movimientos y traslados de una sucursal elegida en un selector (POST).

    En los traslados se incluyen tanto los que salen de la sucursal como los que
    llegan a ella.
    """
    empresa_actual = obtener_empresa(request)

    form = SucursalSelectForm(empresa=empresa_actual)
    movimientos = None
    traslados = None

    if request.method == 'POST':
        form = SucursalSelectForm(request.POST, empresa=empresa_actual)
        if form.is_valid():
            sucursal = form.cleaned_data['sucursal']

            movimientos = MovimientoInventario.objects.filter(
                sucursal=sucursal
            ).select_related('producto', 'usuario').order_by('-fecha')

            traslados = Traslado.objects.filter(
                Q(sucursal_origen=sucursal) | Q(sucursal_destino=sucursal)
            ).select_related('producto', 'sucursal_origen', 'sucursal_destino', 'usuario').order_by('-fecha_creacion')

    return render(request, 'movimientos_por_sucursal.html', {
        'form': form,
        'movimientos': movimientos,
        'traslados': traslados,
    })


@control_acceso('Encargado')
def movimientos_por_producto(request):
    """
    Kardex de un producto elegido en un selector (POST).

    Separa los movimientos "normales" de los generados por traslados y calcula un
    resumen:

    - ``entradas`` / ``salidas``: movimientos normales (sin traslados).
    - ``traslados_salida`` / ``traslados_entrada``: cantidades reales movidas por traslados.
    - ``traslados_pendientes``: unidades en tránsito (enviadas y aún no confirmadas).
    - ``diferencia_traslados``: entregado − recibido en los traslados.
    - ``total_fisico``: entradas + traslados recibidos − salidas − traslados enviados,
      es decir, el stock del producto sumando todas las sucursales.
    """
    empresa_actual = obtener_empresa(request)

    form = ProductoSelectForm(empresa=empresa_actual)

    entradas = None
    salidas = None
    traslados = None
    resumen = {
        'entradas': 0,
        'salidas': 0,
        'traslados_salida': 0,
        'traslados_entrada': 0,
        'traslados_teoricos_salida': 0,
        'traslados_teoricos_entrada': 0,
        'traslados_confirmados': 0,
        'traslados_pendientes': 0,
        'diferencia_traslados': 0,
        'total_fisico': 0,
    }

    if request.method == 'POST':
        form = ProductoSelectForm(request.POST, empresa=empresa_actual)
        if form.is_valid():
            producto = form.cleaned_data['producto']

            # Movimientos normales: se excluyen los que pertenecen a un traslado
            entradas = MovimientoInventario.objects.filter(producto=producto, tipo_movimiento='entrada') \
                .exclude(traslado_entrada__isnull=False).select_related('usuario', 'sucursal').order_by('-fecha')
            salidas = MovimientoInventario.objects.filter(producto=producto, tipo_movimiento='salida') \
                .exclude(traslado_salida__isnull=False).select_related('usuario', 'sucursal').order_by('-fecha')

            traslados = Traslado.objects.filter(producto=producto).select_related(
                'usuario', 'sucursal_origen', 'sucursal_destino'
            ).order_by('-fecha_creacion')

            def _suma(queryset, campo='cantidad'):
                return queryset.aggregate(total=Sum(campo))['total'] or 0

            resumen['entradas'] = _suma(entradas)
            resumen['salidas'] = _suma(salidas)

            # Cantidades reales movidas por traslados (según los movimientos generados)
            resumen['traslados_salida'] = _suma(MovimientoInventario.objects.filter(traslado_salida__producto=producto))
            resumen['traslados_entrada'] = _suma(MovimientoInventario.objects.filter(traslado_entrada__producto=producto))

            # Cantidades declaradas en los traslados
            resumen['traslados_teoricos_salida'] = _suma(traslados, 'cantidad_entregada')
            resumen['traslados_teoricos_entrada'] = _suma(traslados.filter(estado='confirmado'), 'cantidad_recibida')
            resumen['traslados_pendientes'] = _suma(traslados.filter(estado='pendiente'), 'cantidad_entregada')
            resumen['traslados_confirmados'] = resumen['traslados_teoricos_entrada']

            # Stock físico total = entradas + recibido por traslados − salidas − enviado por traslados
            resumen['total_fisico'] = (
                resumen['entradas'] +
                resumen['traslados_entrada'] -
                resumen['salidas'] -
                resumen['traslados_salida']
            )

            resumen['diferencia_traslados'] = (
                resumen['traslados_teoricos_salida'] -
                resumen['traslados_teoricos_entrada']
            )

    return render(request, 'movimientos_por_producto.html', {
        'form': form,
        'entradas': entradas,
        'salidas': salidas,
        'traslados': traslados,
        'resumen': resumen,
    })
