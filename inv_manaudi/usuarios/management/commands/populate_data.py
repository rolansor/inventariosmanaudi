from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
import random

from usuarios.models import Usuario, Empresa, Sucursal, UsuarioPerfil
from productos.models import Producto
from categorias.models import Categoria, Subcategoria, Clase
from inventario.models import Inventario, MovimientoInventario, Traslado


class Command(BaseCommand):
    help = 'Popula la base de datos con datos de prueba para el sistema de inventarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpia todos los datos antes de poblar',
        )
        parser.add_argument(
            '--empresas',
            type=int,
            default=3,
            help='Número de empresas a crear (default: 3)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando población de datos de prueba...'))
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Limpiando datos existentes...'))
            self.limpiar_datos()
        
        with transaction.atomic():
            grupos = self.crear_grupos()
            empresas = self.crear_empresas_y_sucursales(options['empresas'])
            usuarios = self.crear_usuarios(empresas, grupos)
            self.crear_categorias_y_productos(empresas)
            self.crear_inventario_inicial(empresas)
            self.crear_movimientos_ejemplo(empresas)
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Poblacion de datos completada exitosamente!'))
        self.stdout.write(self.style.SUCCESS('\nResumen:'))
        self.stdout.write(f'  - Empresas creadas: {Empresa.objects.count()}')
        self.stdout.write(f'  - Sucursales creadas: {Sucursal.objects.count()}')
        self.stdout.write(f'  - Usuarios creados: {Usuario.objects.count()}')
        self.stdout.write(f'  - Productos creados: {Producto.objects.count()}')
        self.stdout.write(f'  - Inventarios inicializados: {Inventario.objects.count()}')
        self.stdout.write(f'  - Movimientos de ejemplo: {MovimientoInventario.objects.count()}')
        self.stdout.write(self.style.WARNING('\n⚠ IMPORTANTE: Todas las contraseñas son: 1234'))

    def limpiar_datos(self):
        """Limpia todos los datos de prueba"""
        models_to_clear = [
            MovimientoInventario,
            Traslado,
            Inventario,
            Producto,
            Clase,
            Subcategoria,
            Categoria,
            UsuarioPerfil,
            Usuario,
            Sucursal,
            Empresa,
        ]
        
        for model in models_to_clear:
            if model == Usuario:
                # No eliminar superusuarios
                model.objects.filter(is_superuser=False).delete()
            else:
                model.objects.all().delete()
            self.stdout.write(f'  [CLEAR] {model.__name__}')

    def crear_grupos(self):
        """Crea los grupos de permisos si no existen"""
        self.stdout.write("Creando grupos...")
        
        grupos = ['Administrador', 'Supervisor', 'Encargado', 'Manaudi']
        for nombre_grupo in grupos:
            grupo, created = Group.objects.get_or_create(name=nombre_grupo)
            if created:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Grupo '{nombre_grupo}' creado"))
            else:
                self.stdout.write(f"  [INFO] Grupo '{nombre_grupo}' ya existe")
        
        return {g: Group.objects.get(name=g) for g in grupos}

    def crear_empresas_y_sucursales(self, num_empresas=3):
        """Crea empresas con sus sucursales"""
        self.stdout.write("\nCreando empresas y sucursales...")
        
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
        ][:num_empresas]
        
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
            
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] Empresa '{empresa.nombre}' creada con {len(sucursales_data)} sucursales"
            ))
        
        return empresas

    def crear_usuarios(self, empresas, grupos):
        """Crea usuarios para cada rol en cada empresa"""
        self.stdout.write("\nCreando usuarios...")
        
        password = make_password('1234')
        usuarios_creados = []
        
        # Obtener la primera empresa para asignar al superusuario
        primera_empresa = list(empresas.values())[0]['empresa'] if empresas else None
        
        # Mantener o crear el superusuario
        superuser = Usuario.objects.filter(is_superuser=True).first()
        if superuser:
            self.stdout.write(f"  [INFO] Manteniendo superusuario existente: {superuser.username}")
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
                    empresa=primera_empresa,
                    sucursal=None
                )
                self.stdout.write(f"  [INFO] Perfil creado para superusuario")
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
            for grupo in grupos.values():
                superuser.groups.add(grupo)
            if primera_empresa:
                UsuarioPerfil.objects.create(
                    usuario=superuser,
                    empresa=primera_empresa,
                    sucursal=None
                )
            self.stdout.write(self.style.SUCCESS(f"  [OK] Superusuario creado: {superuser.username}"))
        
        # Crear usuarios para cada empresa
        for empresa_nombre, empresa_info in empresas.items():
            empresa = empresa_info['empresa']
            sucursales = empresa_info['sucursales']
            empresa_corto = empresa_nombre.split()[0].lower()[:8]
            
            # Administrador
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
                sucursal=None
            )
            usuarios_creados.append(admin_user)
            
            # Supervisor
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
            
            # Encargado
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
            
            # Manaudi
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
            
            self.stdout.write(self.style.SUCCESS(f"  [OK] 4 usuarios creados para {empresa_nombre}"))
        
        return usuarios_creados

    def crear_categorias_y_productos(self, empresas):
        """Crea categorías, subcategorías, clases y productos de ejemplo para cada empresa"""
        self.stdout.write("\nCreando categorias, subcategorias, clases y productos...")
        
        categorias_base = [
            {
                'codigo': 'ELE',
                'nombre': 'ELECTRÓNICA',
                'subcategorias': [
                    {'codigo': 'COM', 'nombre': 'COMPUTADORAS', 'clases': [
                        {'codigo': 'LAP', 'nombre': 'LAPTOPS'},
                        {'codigo': 'DES', 'nombre': 'DESKTOPS'},
                        {'codigo': 'TAB', 'nombre': 'TABLETS'}
                    ]},
                    {'codigo': 'CEL', 'nombre': 'CELULARES', 'clases': [
                        {'codigo': 'SMA', 'nombre': 'SMARTPHONES'},
                        {'codigo': 'BAS', 'nombre': 'BASICOS'},
                        {'codigo': 'ACC', 'nombre': 'ACCESORIOS CELULAR'}
                    ]}
                ]
            },
            {
                'codigo': 'OFI',
                'nombre': 'OFICINA',
                'subcategorias': [
                    {'codigo': 'PAP', 'nombre': 'PAPELERÍA', 'clases': [
                        {'codigo': 'HOJ', 'nombre': 'PAPEL'},
                        {'codigo': 'CUA', 'nombre': 'CUADERNOS'},
                        {'codigo': 'CAR', 'nombre': 'CARPETAS'}
                    ]},
                    {'codigo': 'MOB', 'nombre': 'MOBILIARIO', 'clases': [
                        {'codigo': 'SIL', 'nombre': 'SILLAS'},
                        {'codigo': 'ESC', 'nombre': 'ESCRITORIOS'},
                        {'codigo': 'ARC', 'nombre': 'ARCHIVADORES'}
                    ]}
                ]
            }
        ]
        
        productos_ejemplo = [
            # Electrónica
            {'codigo': 'LAP001', 'nombre': 'Laptop Dell Latitude', 'precio': 850.00, 'tipo': 'unidad'},
            {'codigo': 'LAP002', 'nombre': 'Laptop HP ProBook', 'precio': 750.00, 'tipo': 'unidad'},
            {'codigo': 'DES001', 'nombre': 'Desktop Dell OptiPlex', 'precio': 650.00, 'tipo': 'unidad'},
            {'codigo': 'TAB001', 'nombre': 'Tablet iPad Air', 'precio': 599.00, 'tipo': 'unidad'},
            {'codigo': 'SMA001', 'nombre': 'iPhone 13', 'precio': 999.00, 'tipo': 'unidad'},
            {'codigo': 'SMA002', 'nombre': 'Samsung Galaxy S21', 'precio': 899.00, 'tipo': 'unidad'},
            # Oficina
            {'codigo': 'HOJ001', 'nombre': 'Resma Papel A4', 'precio': 4.50, 'tipo': 'unidad'},
            {'codigo': 'CUA001', 'nombre': 'Cuaderno 100 hojas', 'precio': 2.50, 'tipo': 'unidad'},
            {'codigo': 'SIL001', 'nombre': 'Silla Ejecutiva', 'precio': 120.00, 'tipo': 'unidad'},
            {'codigo': 'ESC001', 'nombre': 'Escritorio 1.5m', 'precio': 250.00, 'tipo': 'unidad'},
        ]
        
        for empresa_nombre, empresa_info in empresas.items():
            empresa = empresa_info['empresa']
            producto_count = 0
            
            for cat_data in categorias_base:
                categoria = Categoria.objects.create(
                    codigo=cat_data['codigo'],
                    nombre=cat_data['nombre'],
                    empresa=empresa
                )
                
                for subcat_data in cat_data['subcategorias']:
                    subcategoria = Subcategoria.objects.create(
                        codigo=subcat_data['codigo'],
                        nombre=subcat_data['nombre'],
                        categoria=categoria
                    )
                    
                    for clase_data in subcat_data['clases']:
                        clase = Clase.objects.create(
                            codigo=clase_data['codigo'],
                            nombre=clase_data['nombre'],
                            subcategoria=subcategoria
                        )
                        
                        # Crear productos para esta clase
                        for prod_data in productos_ejemplo:
                            if producto_count < 10:  # Limitar productos por empresa
                                codigo_unico = f"{empresa_nombre[:3].upper()}_{prod_data['codigo']}"
                                Producto.objects.create(
                                    codigo=codigo_unico,
                                    nombre=prod_data['nombre'],
                                    precio=Decimal(str(prod_data['precio'])),
                                    tipo_producto=prod_data['tipo'],
                                    clase=clase,
                                    empresa=empresa,
                                    estado='activo',
                                    descripcion=f"Producto de {clase.nombre}"
                                )
                                producto_count += 1
            
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] {producto_count} productos creados para {empresa_nombre}"
            ))

    def crear_inventario_inicial(self, empresas):
        """Crea inventario inicial para los productos"""
        self.stdout.write("\nCreando inventario inicial...")
        
        for empresa_nombre, empresa_info in empresas.items():
            empresa = empresa_info['empresa']
            sucursales = empresa_info['sucursales']
            productos = Producto.objects.filter(empresa=empresa)
            
            for producto in productos:
                for sucursal in sucursales:
                    stock_inicial = random.randint(10, 100)
                    stock_minimo = random.randint(5, 20)
                    
                    Inventario.objects.create(
                        producto=producto,
                        sucursal=sucursal,
                        cantidad=stock_inicial,
                        stock_minimo=stock_minimo
                    )
            
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] Inventario inicializado para {empresa_nombre}"
            ))

    def crear_movimientos_ejemplo(self, empresas):
        """Crea algunos movimientos de ejemplo"""
        self.stdout.write("\nCreando movimientos de ejemplo...")
        
        for empresa_nombre, empresa_info in empresas.items():
            empresa = empresa_info['empresa']
            sucursales = empresa_info['sucursales']
            productos = Producto.objects.filter(empresa=empresa)[:5]  # Solo primeros 5 productos
            usuario = Usuario.objects.filter(
                perfil__empresa=empresa, 
                groups__name='Supervisor'
            ).first()
            
            if not usuario:
                continue
            
            for producto in productos:
                # Crear una entrada
                MovimientoInventario.objects.create(
                    producto=producto,
                    sucursal=sucursales[0],
                    tipo_movimiento='entrada',
                    cantidad=random.randint(10, 50),
                    tipo_documento='factura',
                    documento_respaldo=f'FAC-{random.randint(1000, 9999)}',
                    comentario='Compra de inventario',
                    usuario=usuario
                )
                
                # Crear una salida
                if len(sucursales) > 1:
                    MovimientoInventario.objects.create(
                        producto=producto,
                        sucursal=sucursales[0],
                        tipo_movimiento='salida',
                        cantidad=random.randint(1, 10),
                        tipo_documento='nota_venta',
                        documento_respaldo=f'NV-{random.randint(1000, 9999)}',
                        comentario='Venta al cliente',
                        usuario=usuario
                    )
            
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] Movimientos de ejemplo creados para {empresa_nombre}"
            ))