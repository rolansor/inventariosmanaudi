import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Configurar Django
sys.path.insert(0, 'C:\\Users\\MSHOME\\PycharmProjects\\inventariosmanaudi\\inv_manaudi')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inv_manaudi.settings')
django.setup()

from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from django.db import transaction
from usuarios.models import Usuario, Empresa, Sucursal, UsuarioPerfil
from productos.models import Producto
from categorias.models import Categoria, Subcategoria, Clase
from inventario.models import Inventario, MovimientoInventario, Traslado

def ejecutar_migraciones():
    """Ejecuta makemigrations y migrate"""
    import subprocess
    
    print("Ejecutando migraciones...")
    
    # Cambiar al directorio inv_manaudi
    original_dir = os.getcwd()
    os.chdir('C:\\Users\\MSHOME\\PycharmProjects\\inventariosmanaudi\\inv_manaudi')
    
    try:
        # Ejecutar makemigrations para todas las aplicaciones
        print("  Ejecutando makemigrations...")
        apps = ['usuarios', 'inventario', 'productos', 'categorias', 'auxiliares', 'reportes']
        result = subprocess.run(['python', 'manage.py', 'makemigrations'] + apps, 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  [OK] Migraciones creadas")
            if "No changes detected" in result.stdout:
                print("  [INFO] No se detectaron cambios")
        else:
            print(f"  [ERROR] {result.stderr}")
            
        # Ejecutar migrate
        print("  Ejecutando migrate...")
        result = subprocess.run(['python', 'manage.py', 'migrate'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  [OK] Migraciones aplicadas")
        else:
            print(f"  [ERROR] {result.stderr}")
            
    finally:
        # Volver al directorio original
        os.chdir(original_dir)

def crear_grupos():
    """Crea los grupos de permisos si no existen"""
    print("Creando grupos...")
    
    grupos = ['Administrador', 'Supervisor', 'Encargado', 'Manaudi']
    for nombre_grupo in grupos:
        grupo, created = Group.objects.get_or_create(name=nombre_grupo)
        if created:
            print(f"  [OK] Grupo '{nombre_grupo}' creado")
        else:
            print(f"  [INFO] Grupo '{nombre_grupo}' ya existe")
    
    return {g: Group.objects.get(name=g) for g in grupos}

def crear_empresas_y_sucursales():
    """Crea 3 empresas con sus sucursales"""
    print("\nCreando empresas y sucursales...")
    
    empresas_data = [
        {
            'nombre': 'TechCorp Ecuador',
            'direccion': 'Av. Amazonas N35-17, Quito',
            'telefono': '022501234',
            'email': 'info@techcorp.ec',
            'sucursales': [
                {'nombre': 'Matriz Quito', 'abreviatura': 'UIO', 'tipo': 'bodega'},
                {'nombre': 'Sucursal Guayaquil', 'abreviatura': 'GYE', 'tipo': 'punto_venta'},
                {'nombre': 'Laboratorio Quito', 'abreviatura': 'LAB', 'tipo': 'laboratorio'},
            ]
        },
        {
            'nombre': 'Comercial Andina',
            'direccion': 'Av. 9 de Octubre 729, Guayaquil',
            'telefono': '042301567',
            'email': 'ventas@comercialandina.com',
            'sucursales': [
                {'nombre': 'Bodega Principal', 'abreviatura': 'BOD', 'tipo': 'bodega'},
                {'nombre': 'Punto Venta Norte', 'abreviatura': 'PVN', 'tipo': 'punto_venta'},
                {'nombre': 'Punto Venta Sur', 'abreviatura': 'PVS', 'tipo': 'punto_venta'},
            ]
        },
        {
            'nombre': 'Distribuidora Nacional',
            'direccion': 'Av. Ordoñez Lasso, Cuenca',
            'telefono': '072831999',
            'email': 'contacto@distnacional.ec',
            'sucursales': [
                {'nombre': 'Centro Distribución', 'abreviatura': 'CDI', 'tipo': 'bodega'},
                {'nombre': 'Tienda Cuenca', 'abreviatura': 'CUE', 'tipo': 'punto_venta'},
                {'nombre': 'Tienda Loja', 'abreviatura': 'LOJ', 'tipo': 'punto_venta'},
            ]
        }
    ]
    
    empresas = {}
    for emp_data in empresas_data:
        sucursales_data = emp_data.pop('sucursales')
        empresa = Empresa.objects.create(**emp_data)
        empresas[empresa.nombre] = {'empresa': empresa, 'sucursales': []}
        
        for suc_data in sucursales_data:
            sucursal = Sucursal.objects.create(
                empresa=empresa,
                nombre=suc_data['nombre'],
                abreviatura=suc_data['abreviatura'],
                tipo_sucursal=suc_data['tipo'],
                direccion=f"{suc_data['nombre']} - {empresa.direccion}",
                telefono=empresa.telefono
            )
            empresas[empresa.nombre]['sucursales'].append(sucursal)
        
        print(f"  [OK] Empresa '{empresa.nombre}' creada con {len(sucursales_data)} sucursales")
    
    return empresas

def crear_usuarios(empresas, grupos):
    """Crea usuarios para cada rol en cada empresa"""
    print("\nCreando usuarios...")
    
    password = make_password('1234')
    usuarios_creados = []
    
    # Obtener la primera empresa para asignar al superusuario
    primera_empresa = list(empresas.values())[0]['empresa'] if empresas else None
    
    # Mantener o crear el superusuario
    superuser = Usuario.objects.filter(is_superuser=True).first()
    if superuser:
        print(f"  [INFO] Manteniendo superusuario existente: {superuser.username}")
        # Cambiar contraseña a 1234
        superuser.password = password
        superuser.save()
        # Asegurar que el superusuario tenga todos los grupos
        for grupo in grupos.values():
            superuser.groups.add(grupo)
        # Verificar si tiene perfil, si no crearlo con la primera empresa
        if not hasattr(superuser, 'perfil') and primera_empresa:
            UsuarioPerfil.objects.create(
                usuario=superuser,
                empresa=primera_empresa,  # Asignar primera empresa pero puede ver todas
                sucursal=None
            )
            print(f"  [INFO] Perfil creado para superusuario")
    else:
        # Crear superusuario si no existe
        superuser = Usuario.objects.create(
            username='admin',
            first_name='Super',
            last_name='Admin',
            email='admin@sistema.com',
            password=password,
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        # Asegurar que el superusuario tenga todos los grupos
        for grupo in grupos.values():
            superuser.groups.add(grupo)
        # Crear perfil para el superusuario con la primera empresa
        if primera_empresa:
            UsuarioPerfil.objects.create(
                usuario=superuser,
                empresa=primera_empresa,  # Asignar primera empresa pero puede ver todas
                sucursal=None
            )
        print(f"  [OK] Superusuario creado: {superuser.username}")
    
    # Crear usuarios para cada empresa
    for empresa_nombre, empresa_info in empresas.items():
        empresa = empresa_info['empresa']
        sucursales = empresa_info['sucursales']
        empresa_corto = empresa_nombre.split()[0].lower()[:8]  # Nombre corto para usernames
        
        # Administrador (tiene acceso a toda la empresa)
        admin_user = Usuario.objects.create(
            username=f'{empresa_corto}_admin',
            first_name='Admin',
            last_name=empresa_nombre.split()[0],
            email=f'admin@{empresa_corto}.com',
            password=password,
            is_active=True
        )
        admin_user.groups.add(grupos['Administrador'])
        UsuarioPerfil.objects.create(
            usuario=admin_user,
            empresa=empresa,
            sucursal=None  # Administrador no tiene sucursal específica
        )
        usuarios_creados.append(admin_user)
        
        # Supervisor (asignado a la primera sucursal/bodega)
        supervisor_user = Usuario.objects.create(
            username=f'{empresa_corto}_supervisor',
            first_name='Supervisor',
            last_name=empresa_nombre.split()[0],
            email=f'supervisor@{empresa_corto}.com',
            password=password,
            is_active=True
        )
        supervisor_user.groups.add(grupos['Supervisor'])
        UsuarioPerfil.objects.create(
            usuario=supervisor_user,
            empresa=empresa,
            sucursal=sucursales[0]
        )
        usuarios_creados.append(supervisor_user)
        
        # Encargado (asignado a la segunda sucursal)
        if len(sucursales) > 1:
            encargado_user = Usuario.objects.create(
                username=f'{empresa_corto}_encargado',
                first_name='Encargado',
                last_name=empresa_nombre.split()[0],
                email=f'encargado@{empresa_corto}.com',
                password=password,
                is_active=True
            )
            encargado_user.groups.add(grupos['Encargado'])
            UsuarioPerfil.objects.create(
                usuario=encargado_user,
                empresa=empresa,
                sucursal=sucursales[1]
            )
            usuarios_creados.append(encargado_user)
        
        # Manaudi (usuario especial de auditoría)
        manaudi_user = Usuario.objects.create(
            username=f'{empresa_corto}_manaudi',
            first_name='Manaudi',
            last_name=empresa_nombre.split()[0],
            email=f'manaudi@{empresa_corto}.com',
            password=password,
            is_active=True
        )
        manaudi_user.groups.add(grupos['Manaudi'])
        UsuarioPerfil.objects.create(
            usuario=manaudi_user,
            empresa=empresa,
            sucursal=None
        )
        usuarios_creados.append(manaudi_user)
        
        print(f"  [OK] 4 usuarios creados para {empresa_nombre}")
    
    return usuarios_creados

def crear_categorias_y_productos(empresas):
    """Crea categorías, subcategorías, clases y productos de ejemplo para cada empresa"""
    print("\nCreando categorias, subcategorias, clases y productos...")
    
    # Estructura jerárquica: Categoría > Subcategoría > Clase
    categorias_base = [
        {
            'nombre': 'ELECTRÓNICA',
            'subcategorias': [
                {'nombre': 'COMPUTADORAS', 'clases': ['LAPTOPS', 'DESKTOPS', 'TABLETS']},
                {'nombre': 'CELULARES', 'clases': ['SMARTPHONES', 'BASICOS', 'ACCESORIOS CELULAR']},
                {'nombre': 'ACCESORIOS', 'clases': ['MOUSE', 'TECLADOS', 'CABLES']}
            ]
        },
        {
            'nombre': 'OFICINA',
            'subcategorias': [
                {'nombre': 'PAPELERÍA', 'clases': ['PAPEL', 'CUADERNOS', 'CARPETAS']},
                {'nombre': 'MOBILIARIO', 'clases': ['SILLAS', 'ESCRITORIOS', 'ARCHIVADORES']},
                {'nombre': 'SUMINISTROS', 'clases': ['TONERS', 'TINTAS', 'GRAPAS']}
            ]
        },
        {
            'nombre': 'LIMPIEZA',
            'subcategorias': [
                {'nombre': 'DETERGENTES', 'clases': ['LIQUIDOS', 'POLVO', 'CONCENTRADOS']},
                {'nombre': 'DESINFECTANTES', 'clases': ['ALCOHOL', 'CLORO', 'ANTIBACTERIAL']},
                {'nombre': 'UTENSILIOS', 'clases': ['ESCOBAS', 'TRAPEADORES', 'PAÑOS']}
            ]
        }
    ]
    
    # Productos actualizados con clases
    productos_base = [
        # Electrónica
        {'codigo': 'LAP001', 'nombre': 'Laptop Dell Inspiron', 'precio': 850.00, 'categoria': 'ELECTRÓNICA', 'subcategoria': 'COMPUTADORAS', 'clase': 'LAPTOPS'},
        {'codigo': 'CEL001', 'nombre': 'iPhone 13', 'precio': 999.00, 'categoria': 'ELECTRÓNICA', 'subcategoria': 'CELULARES', 'clase': 'SMARTPHONES'},
        {'codigo': 'MOU001', 'nombre': 'Mouse Inalámbrico', 'precio': 25.00, 'categoria': 'ELECTRÓNICA', 'subcategoria': 'ACCESORIOS', 'clase': 'MOUSE'},
        # Oficina
        {'codigo': 'PAP001', 'nombre': 'Resma Papel A4', 'precio': 4.50, 'categoria': 'OFICINA', 'subcategoria': 'PAPELERÍA', 'clase': 'PAPEL'},
        {'codigo': 'SIL001', 'nombre': 'Silla Ejecutiva', 'precio': 150.00, 'categoria': 'OFICINA', 'subcategoria': 'MOBILIARIO', 'clase': 'SILLAS'},
        {'codigo': 'TON001', 'nombre': 'Toner HP', 'precio': 75.00, 'categoria': 'OFICINA', 'subcategoria': 'SUMINISTROS', 'clase': 'TONERS'},
        # Limpieza
        {'codigo': 'DET001', 'nombre': 'Detergente Industrial 5L', 'precio': 12.00, 'categoria': 'LIMPIEZA', 'subcategoria': 'DETERGENTES', 'clase': 'LIQUIDOS'},
        {'codigo': 'ALC001', 'nombre': 'Alcohol 70% 1L', 'precio': 3.50, 'categoria': 'LIMPIEZA', 'subcategoria': 'DESINFECTANTES', 'clase': 'ALCOHOL'},
        {'codigo': 'ESC001', 'nombre': 'Escoba Industrial', 'precio': 8.00, 'categoria': 'LIMPIEZA', 'subcategoria': 'UTENSILIOS', 'clase': 'ESCOBAS'},
    ]
    
    for empresa_nombre, empresa_info in empresas.items():
        empresa = empresa_info['empresa']
        sucursales = empresa_info['sucursales']
        
        # Crear categorías, subcategorías y clases
        clases_map = {}  # Mapa para encontrar clases fácilmente
        
        for cat_data in categorias_base:
            categoria = Categoria.objects.create(
                nombre=cat_data['nombre'],
                empresa=empresa
            )
            
            for subcat_data in cat_data['subcategorias']:
                subcategoria = Subcategoria.objects.create(
                    nombre=subcat_data['nombre'],
                    categoria=categoria
                )
                
                for clase_nombre in subcat_data['clases']:
                    clase = Clase.objects.create(
                        nombre=clase_nombre,
                        subcategoria=subcategoria
                    )
                    # Crear clave única para mapear
                    clave = f"{cat_data['nombre']}_{subcat_data['nombre']}_{clase_nombre}"
                    clases_map[clave] = clase
        
        # Crear productos
        productos_creados = []
        for prod_data in productos_base:
            # Buscar la clase correspondiente
            clave = f"{prod_data['categoria']}_{prod_data['subcategoria']}_{prod_data['clase']}"
            clase = clases_map.get(clave)
            
            if clase:
                producto = Producto.objects.create(
                    codigo=f"{empresa_nombre[:3].upper()}-{prod_data['codigo']}",
                    nombre=prod_data['nombre'],
                    descripcion=f"{prod_data['nombre']} - {empresa_nombre}",
                    precio=Decimal(str(prod_data['precio'])),
                    tipo_producto='unidad',
                    clase=clase,  # Ahora apunta a Clase en lugar de Subcategoria
                    empresa=empresa,
                    estado='activo'
                )
                productos_creados.append(producto)
                
                # Crear inventario inicial en cada sucursal
                for sucursal in sucursales:
                    cantidad_inicial = random.randint(10, 100)
                    Inventario.objects.create(
                        producto=producto,
                        sucursal=sucursal,
                        cantidad=cantidad_inicial,
                        stock_minimo=10
                    )
        
        print(f"  [OK] {len(productos_creados)} productos creados para {empresa_nombre}")
        print(f"      con {Categoria.objects.filter(empresa=empresa).count()} categorías,")
        print(f"      {Subcategoria.objects.filter(categoria__empresa=empresa).count()} subcategorías y")
        print(f"      {Clase.objects.filter(subcategoria__categoria__empresa=empresa).count()} clases")
    
    return productos_creados

def crear_movimientos_y_traslados(empresas):
    """Crea movimientos de inventario y traslados de ejemplo"""
    print("\nCreando movimientos y traslados...")
    
    for empresa_nombre, empresa_info in empresas.items():
        empresa = empresa_info['empresa']
        sucursales = empresa_info['sucursales']
        
        if len(sucursales) < 2:
            continue
            
        # Obtener algunos productos de la empresa
        productos = Producto.objects.filter(empresa=empresa)[:3]
        
        # Obtener usuarios de la empresa
        supervisor = Usuario.objects.filter(
            perfil__empresa=empresa,
            groups__name='Supervisor'
        ).first()
        
        encargado = Usuario.objects.filter(
            perfil__empresa=empresa,
            groups__name='Encargado'
        ).first()
        
        if not supervisor or not encargado:
            continue
        
        # Crear algunos movimientos de entrada
        for producto in productos:
            MovimientoInventario.objects.create(
                producto=producto,
                sucursal=sucursales[0],
                tipo_movimiento='entrada',
                cantidad=50,
                tipo_documento='factura',
                documento_respaldo=f'FAC-{random.randint(1000, 9999)}',
                comentario='Compra inicial de inventario',
                usuario=supervisor
            )
        
        # Crear algunos movimientos de salida
        for producto in productos[:2]:
            MovimientoInventario.objects.create(
                producto=producto,
                sucursal=sucursales[0],
                tipo_movimiento='salida',
                cantidad=10,
                tipo_documento='nota_venta',
                documento_respaldo=f'NV-{random.randint(1000, 9999)}',
                comentario='Venta a cliente',
                usuario=encargado if encargado else supervisor
            )
        
        # Crear un traslado pendiente
        if len(productos) > 0:
            traslado = Traslado.objects.create(
                producto=productos[0],
                sucursal_origen=sucursales[0],
                sucursal_destino=sucursales[1],
                cantidad_entregada=20,
                usuario=supervisor,
                estado='pendiente',
                tipo_documento='guia_remision',
                documento_respaldo='GR-001'
            )
            
            # Crear uno confirmado
            if len(productos) > 1:
                traslado_confirmado = Traslado.objects.create(
                    producto=productos[1],
                    sucursal_origen=sucursales[0],
                    sucursal_destino=sucursales[1],
                    cantidad_entregada=15,
                    cantidad_recibida=15,
                    usuario=supervisor,
                    estado='confirmado',
                    tipo_documento='guia_remision',
                    documento_respaldo='GR-002'
                )
        
        print(f"  [OK] Movimientos y traslados creados para {empresa_nombre}")

def mostrar_resumen():
    """Muestra un resumen de los datos creados"""
    print("\n" + "="*60)
    print("RESUMEN DE DATOS CREADOS")
    print("="*60)
    
    print(f"\nEmpresas: {Empresa.objects.count()}")
    for empresa in Empresa.objects.all():
        sucursales = Sucursal.objects.filter(empresa=empresa)
        print(f"  - {empresa.nombre}: {sucursales.count()} sucursales")
    
    print(f"\nUsuarios: {Usuario.objects.count()}")
    for grupo in Group.objects.all():
        usuarios = Usuario.objects.filter(groups=grupo)
        print(f"  - {grupo.name}: {usuarios.count()} usuarios")
    
    print(f"\nProductos: {Producto.objects.count()}")
    print(f"Movimientos: {MovimientoInventario.objects.count()}")
    print(f"Traslados: {Traslado.objects.count()}")
    print(f"  - Pendientes: {Traslado.objects.filter(estado='pendiente').count()}")
    print(f"  - Confirmados: {Traslado.objects.filter(estado='confirmado').count()}")
    
    print("\n" + "="*60)
    print("CREDENCIALES DE ACCESO")
    print("="*60)
    print("\n[IMPORTANTE] Todas las contrasenas son: 1234\n")
    
    print("SUPERUSUARIO:")
    superuser = Usuario.objects.filter(is_superuser=True).first()
    if superuser:
        print(f"  - {superuser.username} (acceso total a todas las empresas)")
    
    for empresa in Empresa.objects.all():
        print(f"\n{empresa.nombre.upper()}:")
        usuarios = Usuario.objects.filter(perfil__empresa=empresa).order_by('groups__name')
        for usuario in usuarios:
            grupos = ", ".join([g.name for g in usuario.groups.all()])
            sucursal = usuario.perfil.sucursal.nombre if usuario.perfil.sucursal else "N/A"
            print(f"  - {usuario.username} ({grupos}) - Sucursal: {sucursal}")
    
    print("\n[OK] Poblacion de datos completada exitosamente!")

def main():
    """Función principal"""
    print("INICIANDO POBLACION DE DATOS DE PRUEBA")
    print("="*60)
    
    try:
        with transaction.atomic():
            # Primero ejecutar migraciones
            ejecutar_migraciones()

            # Crear estructura
            grupos = crear_grupos()
            empresas = crear_empresas_y_sucursales()
            usuarios = crear_usuarios(empresas, grupos)
            productos = crear_categorias_y_productos(empresas)
            crear_movimientos_y_traslados(empresas)
            
            # Mostrar resumen
            mostrar_resumen()
            
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        print("Revirtiendo cambios...")
        raise

if __name__ == "__main__":
    main()