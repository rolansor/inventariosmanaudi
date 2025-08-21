from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from productos.models import Producto
from usuarios.models import Sucursal
from usuarios.views import obtener_empresa
from usuarios.templatetags.tags import control_acceso
from .models import MovimientoInventario, Traslado
from .forms import MovimientoInventarioForm, ProductoSelectForm, SucursalSelectForm, TrasladoForm, \
    ConfirmarRecepcionForm


def movimiento_inventario(request):
    empresa_actual = obtener_empresa(request)

    if request.method == 'POST':
        # Inicializar el formulario con los datos del POST y los archivos
        form = MovimientoInventarioForm(request.POST, request.FILES, user=request.user)
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
        # Inicializar el formulario sin datos de POST
        form = MovimientoInventarioForm(user=request.user)

    # Mostrar solo los últimos 10 movimientos de la empresa del usuario logueado
    movimientos = MovimientoInventario.objects.filter(producto__empresa=empresa_actual).order_by('-fecha')[:20]

    return render(request, 'movimiento_inventario.html', {
        'form': form,
        'movimientos': movimientos,
    })


@control_acceso('Supervisor')
def iniciar_traslado(request):
    empresa_actual = obtener_empresa(request)

    if request.method == 'POST':
        form = TrasladoForm(request.POST)
        # Aplicar filtros de productos y sucursales según la empresa actual
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_origen'].queryset = Sucursal.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa_actual)

        if form.is_valid():
            traslado = form.save(commit=False)  # No se guarda aún en la base de datos
            traslado.usuario = request.user  # Asignar el usuario que inicia el traslado

            try:
                traslado.save()  # Guardar el traslado
                messages.success(request, 'Traslado iniciado exitosamente.')
                return redirect('traslados_pendientes')  # Redireccionar después de guardar
            except ValueError as e:
                form.add_error(None, str(e))  # Manejar errores con un mensaje adecuado
        else:
            messages.error(request, 'Por favor, corrige los errores indicados.')

    else:
        form = TrasladoForm()
        # Filtrar productos y sucursales por la empresa actual
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_origen'].queryset = Sucursal.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa_actual)

    # Obtener los últimos 10 traslados
    traslados_recientes = Traslado.objects.filter(producto__empresa=empresa_actual).order_by('-fecha_creacion')[:10]

    return render(request, 'iniciar_traslado.html', {
        'form': form,
        'traslados_recientes': traslados_recientes,  # Pasamos los traslados a la plantilla
    })


@control_acceso('Encargado')
def iniciar_traslado_laboratorio(request):
    empresa_actual = obtener_empresa(request)
    sucursal_usuario = request.user.perfil.sucursal
    tipo_sucursal_usuario = sucursal_usuario.tipo_sucursal if sucursal_usuario else None

    if request.method == 'POST':
        form = TrasladoForm(request.POST)
        if form.is_valid():
            traslado = form.save(commit=False)
            traslado.usuario = request.user
            traslado.save()
            messages.success(request, 'Traslado registrado exitosamente.')
            return redirect('traslados_pendientes')
        else:
            messages.error(request, 'Por favor, corrige los errores indicados.')
    else:
        form = TrasladoForm()
        # Filtrado dinámico de opciones de sucursales de origen y destino
        if tipo_sucursal_usuario == 'laboratorio':
            # Si el usuario está en un laboratorio, sólo puede hacer traslados de regreso a bodegas o puntos de venta
            form.fields['sucursal_origen'].queryset = Sucursal.objects.filter(id=sucursal_usuario.id)
            form.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa_actual, tipo_sucursal__in=['bodega', 'punto_venta'])
        else:
            # Si el usuario está en una bodega o punto de venta, puede enviar a laboratorios
            form.fields['sucursal_origen'].queryset = Sucursal.objects.filter(id=sucursal_usuario.id)
            form.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa_actual, tipo_sucursal='laboratorio')
            # Filtrar productos con stock en la sucursal del usuario (sucursal_origen)
            # Filtrar productos con inventario disponible en la sucursal actual del usuario
            form.fields['producto'].queryset = Producto.objects.filter(
                inventarios__sucursal=sucursal_usuario,
                inventarios__cantidad__gt=0
            ).distinct()
        form.fields['tipo_documento'].choices = [choice for choice in Traslado.TIPO_DOCUMENTO_CHOICES if choice[0] == 'orden_trabajo']
    return render(request, 'iniciar_traslado_laboratorio.html', {'form': form})


@control_acceso('Encargado')
def traslados_pendientes(request):
    empresa_actual = obtener_empresa(request)
    sucursal_usuario = request.user.perfil.sucursal

    # Verificar si el usuario pertenece al grupo "Supervisor"
    if request.user.groups.filter(name="Supervisor").exists():
        # Si es supervisor, mostrar todos los traslados de la empresa actual
        movimientos_pendientes = Traslado.objects.filter(producto__empresa=empresa_actual, estado='pendiente').order_by('-fecha_creacion')
    else:
        # Si no es supervisor, mostrar solo los traslados asociados al usuario actual
        movimientos_pendientes = Traslado.objects.filter(producto__empresa=empresa_actual, sucursal_destino=sucursal_usuario, estado='pendiente').order_by('-fecha_creacion')
    return render(request, 'traslados_pendientes.html', {'movimientos_pendientes': movimientos_pendientes})


@control_acceso('Encargado')
def confirmar_traslado(request, pk):
    movimiento = get_object_or_404(Traslado, pk=pk, estado='pendiente')
    # Obtener la sucursal del usuario logueado (suponiendo que el perfil del usuario tiene el campo sucursal)
    sucursal_usuario = request.user.perfil.sucursal
    # Validar si la sucursal de destino es la misma que la sucursal del usuario
    if movimiento.sucursal_destino != sucursal_usuario:
        messages.error(request, 'No tienes permiso para confirmar este traslado.')
        return redirect('traslados_pendientes')

    if request.method == 'POST':
        form = ConfirmarRecepcionForm(request.POST, instance=movimiento)
        if form.is_valid():
            try:
                movimiento.confirmar()
                messages.success(request, 'Recepción confirmada exitosamente.')
                return redirect('traslados_pendientes')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = ConfirmarRecepcionForm(instance=movimiento)

    return render(request, 'confirmar_traslado.html', {
        'form': form,
        'movimiento': movimiento,
    })


@control_acceso('Supervisor')
def movimientos_por_empresa(request):
    """
    Vista para mostrar todos los movimientos y traslados de una empresa, solo accesible para usuarios del grupo 'Manaudi'.
    """
    empresa_actual = obtener_empresa(request)
    sucursales = Sucursal.objects.filter(empresa=empresa_actual)

    # Movimientos de inventario (entradas y salidas)
    movimientos = MovimientoInventario.objects.filter(sucursal__in=sucursales).order_by('-fecha')

    # Traslados de salida (traslados realizados desde la empresa actual)
    traslados = Traslado.objects.filter(producto__empresa=empresa_actual).order_by('-fecha_creacion')

    return render(request, 'movimientos_por_empresa.html', {
        'movimientos': movimientos,
        'traslados': traslados,
        'empresa': empresa_actual,
    })


@control_acceso('Supervisor')
def movimientos_por_sucursal(request):
    """
    Vista que muestra los movimientos de inventario y traslados para una sucursal específica.
    """
    # Obtener la empresa del usuario actual
    empresa_actual = obtener_empresa(request)

    # Inicializar formulario para seleccionar sucursal
    form = SucursalSelectForm(empresa=empresa_actual)
    movimientos = None
    traslados = None

    if request.method == 'POST':
        form = SucursalSelectForm(request.POST, empresa=empresa_actual)
        if form.is_valid():
            sucursal = form.cleaned_data['sucursal']

            # Filtrar solo los movimientos de la sucursal seleccionada
            movimientos = MovimientoInventario.objects.filter(sucursal=sucursal).order_by('-fecha')

            # Filtrar los traslados donde la sucursal seleccionada es la de origen o destino
            traslados = Traslado.objects.filter(sucursal_origen=sucursal).order_by('-fecha_creacion')

    return render(request, 'movimientos_por_sucursal.html', {
        'form': form,
        'movimientos': movimientos,
        'traslados': traslados,
    })


@control_acceso('Encargado')
def movimientos_por_producto(request):
    # Obtener la empresa del usuario actual
    empresa_actual = obtener_empresa(request)

    # Inicializar el formulario con los productos filtrados por empresa
    form = ProductoSelectForm(empresa=empresa_actual)

    entradas = None
    salidas = None
    traslados_salida = None
    traslados_entrada = None
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

            # Filtrar los movimientos por tipo (entrada y salida) excluyendo aquellos relacionados a traslados
            entradas = MovimientoInventario.objects.filter(producto=producto, tipo_movimiento='entrada') \
                .exclude(traslado_entrada__isnull=False).order_by('-fecha')
            salidas = MovimientoInventario.objects.filter(producto=producto, tipo_movimiento='salida') \
                .exclude(traslado_salida__isnull=False).order_by('-fecha')

            traslados = Traslado.objects.filter(producto=producto).order_by('-fecha_creacion')
            traslados_confirmados = Traslado.objects.filter(producto=producto, estado='confirmado').order_by('-fecha_creacion')
            traslados_pendientes = Traslado.objects.filter(producto=producto, movimiento_salida__isnull=False, estado='pendiente').order_by('-fecha_creacion')

            traslados_teoricos_salida = Traslado.objects.filter(producto=producto).aggregate(
                total=models.Sum('cantidad_entregada'))['total'] or 0
            resumen['traslados_teoricos_salida'] = traslados_teoricos_salida
            traslados_teoricos_entrada = Traslado.objects.filter(producto=producto).aggregate(
                total=models.Sum('cantidad_recibida'))['total'] or 0
            resumen['traslados_teoricos_entrada'] = traslados_teoricos_entrada

            traslados_salida= MovimientoInventario.objects.filter(traslado_salida__producto=producto).aggregate(
                total=models.Sum('cantidad'))['total'] or 0
            resumen['traslados_salida'] = traslados_salida

            traslados_entrada = MovimientoInventario.objects.filter(traslado_entrada__producto=producto).aggregate(
                total=models.Sum('cantidad'))['total'] or 0
            resumen['traslados_entrada'] = traslados_entrada

            # Calcular los totales de entradas, salidas, y traslados
            resumen['entradas'] = entradas.aggregate(total=models.Sum('cantidad'))['total'] or 0
            resumen['salidas'] = salidas.aggregate(total=models.Sum('cantidad'))['total'] or 0

            # Calcular los totales pendientes de confirmar
            resumen['traslados_pendientes'] = traslados_pendientes.aggregate(total=models.Sum('cantidad_entregada'))['total'] or 0
            resumen['traslados_confirmados'] = traslados_confirmados.aggregate(total=models.Sum('cantidad_recibida'))['total'] or 0

            # Calcular el total físico disponible (entradas + traslados de entrada - salidas - traslados de salida)
            resumen['total_fisico'] = resumen['entradas'] - resumen['salidas'] - resumen['traslados_pendientes']

            # Calcular el excedente o faltante (físico - pendiente de confirmar)
            resumen['diferencia_traslados'] = resumen['traslados_salida'] - resumen['traslados_entrada'] - resumen['traslados_pendientes']

    return render(request, 'movimientos_por_producto.html', {
        'form': form,
        'entradas': entradas,
        'salidas': salidas,
        'traslados_salida': traslados_salida,
        'traslados_entrada': traslados_entrada,
        'traslados': traslados,
        'resumen': resumen,
    })
