from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from usuarios.models import Usuario, Empresa, Sucursal, UsuarioPerfil
from productos.models import Producto
from inventario.models import Traslado, MovimientoInventario, Inventario
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Poblar la base de datos con datos del JSON original'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            self.stdout.write('Iniciando población de base de datos desde JSON...')
            
            # Crear grupos
            self.stdout.write('Creando grupos de usuarios...')
            grupos = self.crear_grupos()
            
            # Crear empresa
            self.stdout.write('Creando empresa NINEFIFTEEN...')
            empresa = self.crear_empresa()
            
            # Crear sucursales
            self.stdout.write('Creando sucursales...')
            sucursales = self.crear_sucursales(empresa)
            
            # Crear usuarios
            self.stdout.write('Creando usuarios...')
            usuarios = self.crear_usuarios(empresa, sucursales, grupos)
            
            # Crear productos de óptica
            self.stdout.write('Creando productos de óptica...')
            productos = self.crear_productos_optica(empresa)
            
            # Crear inventarios iniciales
            self.stdout.write('Creando inventarios iniciales...')
            self.crear_inventarios_iniciales(sucursales, productos)
            
            # Crear algunos traslados de ejemplo
            self.stdout.write('Creando traslados de ejemplo...')
            self.crear_traslados_ejemplo(sucursales, productos, usuarios)
            
            self.stdout.write(self.style.SUCCESS('+ Base de datos poblada exitosamente!'))
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write(self.style.SUCCESS('EMPRESA: NINEFIFTEEN'))
            self.stdout.write(self.style.SUCCESS('USUARIOS CREADOS (todos con password: 1234):'))
            self.stdout.write(self.style.SUCCESS('  administrador_inventarios (Administrador)'))
            self.stdout.write(self.style.SUCCESS('  ninefifteen_manaudi (Manaudi)'))
            self.stdout.write(self.style.SUCCESS('  ninefifteen_guayaquil (Supervisor)'))
            self.stdout.write(self.style.SUCCESS('  ninefifteen_quito (Encargado)'))
            self.stdout.write(self.style.SUCCESS('  ninefifteen_cuenca (Encargado)'))
            self.stdout.write(self.style.SUCCESS('  ninefifteen_administrador (Supervisor)'))
            self.stdout.write(self.style.SUCCESS('  ninefifteen_labgye (Encargado)'))
            self.stdout.write(self.style.SUCCESS('='*60))
    
    def crear_grupos(self):
        """Crear grupos según auth_group del JSON"""
        grupos_data = [
            {'id': 1, 'name': 'Administrador'},
            {'id': 2, 'name': 'Manaudi'},
            {'id': 3, 'name': 'Supervisor'},
            {'id': 4, 'name': 'Encargado'},
        ]
        
        grupos = {}
        for data in grupos_data:
            grupo, created = Group.objects.get_or_create(
                name=data['name']
            )
            grupos[data['id']] = grupo
            grupos[data['name']] = grupo
            if created:
                self.stdout.write(f'  + Grupo "{data["name"]}" creado')
            else:
                self.stdout.write(f'  - Grupo "{data["name"]}" ya existe')
        
        return grupos
    
    def crear_empresa(self):
        """Crear empresa según usuarios_empresa del JSON"""
        empresa, created = Empresa.objects.get_or_create(
            nombre='NINEFIFTEEN',
            defaults={
                'direccion': 'Guayaquil',
                'telefono': '042222222',
                'email': 'ninefifteen@hotmail.com'
            }
        )
        if created:
            self.stdout.write(f'  + Empresa "{empresa.nombre}" creada')
        else:
            self.stdout.write(f'  - Empresa "{empresa.nombre}" ya existe')
        
        return empresa
    
    def crear_sucursales(self, empresa):
        """Crear sucursales según usuarios_sucursal del JSON"""
        sucursales_data = [
            {
                'id': 1, 'nombre': 'Guayaquil', 'abreviatura': 'GYQ',
                'direccion': 'Guayaquil', 'telefono': '042222222', 'tipo_sucursal': 'punto_venta'
            },
            {
                'id': 2, 'nombre': 'Quito', 'abreviatura': 'UIO',
                'direccion': 'Quito', 'telefono': '042222222', 'tipo_sucursal': 'punto_venta'
            },
            {
                'id': 3, 'nombre': 'Cuenca', 'abreviatura': 'CUE',
                'direccion': 'Cuenca', 'telefono': '042222222', 'tipo_sucursal': 'punto_venta'
            },
            {
                'id': 4, 'nombre': 'Laboratorio Guayaquil', 'abreviatura': 'LGQ',
                'direccion': 'Guayaquil', 'telefono': '042222222', 'tipo_sucursal': 'laboratorio'
            },
            {
                'id': 5, 'nombre': 'Laboratorio Cuenca', 'abreviatura': 'LCU',
                'direccion': 'Cuenca', 'telefono': '042222222', 'tipo_sucursal': 'laboratorio'
            },
            {
                'id': 6, 'nombre': 'Laboratorio Quito', 'abreviatura': 'LQU',
                'direccion': 'Quito', 'telefono': '042222222', 'tipo_sucursal': 'laboratorio'
            }
        ]
        
        sucursales = {}
        for data in sucursales_data:
            sucursal, created = Sucursal.objects.get_or_create(
                empresa=empresa,
                nombre=data['nombre'],
                defaults={
                    'abreviatura': data['abreviatura'],
                    'direccion': data['direccion'],
                    'telefono': data['telefono'],
                    'tipo_sucursal': data['tipo_sucursal']
                }
            )
            sucursales[data['id']] = sucursal
            sucursales[data['nombre']] = sucursal
            if created:
                self.stdout.write(f'  + Sucursal "{sucursal.nombre}" creada')
            else:
                self.stdout.write(f'  - Sucursal "{sucursal.nombre}" ya existe')
        
        return sucursales
    
    def crear_usuarios(self, empresa, sucursales, grupos):
        """Crear usuarios según usuarios_usuario del JSON"""
        usuarios_data = [
            {
                'id': 1, 'username': 'administrador_inventarios',
                'first_name': 'Edgar', 'last_name': 'Rivas',
                'email': 'edgar.rivas@manaudi.com.ec',
                'telefono': '0990464145', 'direccion': 'ayacucho 714 y Callejon Octava',
                'is_staff': True, 'is_superuser': True, 'is_active': True,
                'grupos': [1], 'sucursal_id': None  # Administrador + Supervisor
            },
            {
                'id': 2, 'username': 'ninefifteen_manaudi',
                'first_name': 'Manaudi', 'last_name': 'Ninefifteen',
                'email': 'ninefifteen@hotmail.com',
                'telefono': '042222222', 'direccion': 'Guayaquil',
                'is_staff': False, 'is_superuser': False, 'is_active': True,
                'grupos': [2], 'sucursal_id': None
            },
            {
                'id': 3, 'username': 'ninefifteen_guayaquil',
                'first_name': 'Usuario', 'last_name': 'Guayaquil',
                'email': 'ninefifteen@hotmail.com',
                'telefono': '042222222', 'direccion': 'Guayaquil',
                'is_staff': False, 'is_superuser': False, 'is_active': True,
                'grupos': [3], 'sucursal_id': 1
            },
            {
                'id': 5, 'username': 'ninefifteen_cuenca',
                'first_name': 'Usuario', 'last_name': 'Cuenca',
                'email': 'ninefifteen@hotmail.com',
                'telefono': '042222222', 'direccion': 'Cuenca',
                'is_staff': False, 'is_superuser': False, 'is_active': True,
                'grupos': [4], 'sucursal_id': 3
            },
            {
                'id': 6, 'username': 'ninefifteen_quito',
                'first_name': 'Usuario', 'last_name': 'Quito',
                'email': 'ninefifteen@hotmail.com',
                'telefono': '042222222', 'direccion': 'Quito',
                'is_staff': False, 'is_superuser': False, 'is_active': True,
                'grupos': [4], 'sucursal_id': 2
            },
            {
                'id': 7, 'username': 'ninefifteen_administrador',
                'first_name': 'Stephanny', 'last_name': '',
                'email': 'ninefifteen@hotmail.com',
                'telefono': '042222222', 'direccion': 'Guayaquil',
                'is_staff': False, 'is_superuser': False, 'is_active': True,
                'grupos': [3], 'sucursal_id': 1
            },
            {
                'id': 29, 'username': 'ninefifteen_labgye',
                'first_name': 'Laboratorio Guayaquil', 'last_name': 'Ninefifteen',
                'email': 'ninefifteen@hotmail.com',
                'telefono': '042222222', 'direccion': 'Guayaquil',
                'is_staff': False, 'is_superuser': False, 'is_active': True,
                'grupos': [4], 'sucursal_id': 4
            }
        ]
        
        usuarios = {}
        for data in usuarios_data:
            usuario, created = Usuario.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'telefono': data['telefono'],
                    'direccion': data['direccion'],
                    'is_staff': data['is_staff'],
                    'is_superuser': data['is_superuser'],
                    'is_active': data['is_active']
                }
            )
            
            if created:
                # Establecer contraseña simple para todos
                usuario.set_password('1234')
                usuario.save()
                
                # Agregar a grupos
                for grupo_id in data['grupos']:
                    grupo = grupos[grupo_id]
                    usuario.groups.add(grupo)
                
                # Crear perfil
                sucursal = sucursales.get(data['sucursal_id']) if data['sucursal_id'] else None
                UsuarioPerfil.objects.create(
                    usuario=usuario,
                    empresa=empresa,
                    sucursal=sucursal
                )
                
                self.stdout.write(f'  + Usuario "{usuario.username}" creado')
            else:
                self.stdout.write(f'  - Usuario "{usuario.username}" ya existe')
            
            usuarios[data['id']] = usuario
            usuarios[data['username']] = usuario
        
        return usuarios
    
    def crear_productos_optica(self, empresa):
        """Crear productos de óptica de ejemplo"""
        productos_data = [
            # Marcos económicos
            {
                'linea': '90', 'sublinea': '01', 'clase': '01',
                'marca': 'RAY-BAN', 'modelo': 'RB3025',
                'precio': Decimal('89.99'), 'tipo_producto': 'UNIDAD',
                'material': 'METAL', 'nombre': 'AVIADOR CLÁSICO',
                'descripcion': 'MARCO AVIADOR CLÁSICO PARA HOMBRE'
            },
            {
                'linea': '90', 'sublinea': '02', 'clase': '01',
                'marca': 'VOGUE', 'modelo': 'VO5239',
                'precio': Decimal('75.50'), 'tipo_producto': 'UNIDAD',
                'material': 'PASTA', 'nombre': 'CAT EYE FASHION',
                'descripcion': 'MARCO CAT EYE PARA MUJER'
            },
            {
                'linea': '90', 'sublinea': '05', 'clase': '02',
                'marca': 'OAKLEY', 'modelo': 'OX8046',
                'precio': Decimal('120.00'), 'tipo_producto': 'UNIDAD',
                'material': 'ACETATO', 'nombre': 'DEPORTIVO UNISEX',
                'descripcion': 'MARCO DEPORTIVO RESISTENTE'
            },
            {
                'linea': '91', 'sublinea': '01', 'clase': '03',
                'marca': 'PRADA', 'modelo': 'PR17WS',
                'precio': Decimal('350.00'), 'tipo_producto': 'UNIDAD',
                'material': 'METAL', 'nombre': 'EJECUTIVO PREMIUM',
                'descripcion': 'MARCO EJECUTIVO DE LUJO'
            },
            {
                'linea': '91', 'sublinea': '02', 'clase': '03',
                'marca': 'CHANEL', 'modelo': 'CH5380',
                'precio': Decimal('450.00'), 'tipo_producto': 'UNIDAD',
                'material': 'ACETATO', 'nombre': 'GLAMOUR EXCLUSIVE',
                'descripcion': 'MARCO DE DISEÑADOR PARA MUJER'
            },
            {
                'linea': '92', 'sublinea': '05', 'clase': '03',
                'marca': 'TOM FORD', 'modelo': 'TF5634',
                'precio': Decimal('580.00'), 'tipo_producto': 'UNIDAD',
                'material': 'METAL', 'nombre': 'LUXURY EDITION',
                'descripcion': 'MARCO DE ALTA GAMA EDICIÓN LIMITADA'
            },
            {
                'linea': '93', 'sublinea': '05', 'clase': '01',
                'marca': 'GENERIC', 'modelo': 'CASE-001',
                'precio': Decimal('10.00'), 'tipo_producto': 'UNIDAD',
                'material': None, 'nombre': 'ESTUCHE RÍGIDO',
                'descripcion': 'ESTUCHE PROTECTOR PARA LENTES'
            }
        ]
        
        productos = []
        for data in productos_data:
            producto, created = Producto.objects.get_or_create(
                empresa=empresa,
                linea=data['linea'],
                sublinea=data['sublinea'],
                clase=data['clase'],
                marca=data['marca'],
                modelo=data['modelo'],
                defaults={
                    'precio': data['precio'],
                    'tipo_producto': data['tipo_producto'],
                    'material': data.get('material'),
                    'nombre': data.get('nombre'),
                    'descripcion': data.get('descripcion'),
                    'estado': 'activo'
                }
            )
            
            productos.append(producto)
            if created:
                self.stdout.write(f'  + Producto "{producto.marca} {producto.modelo}" (Código: {producto.codigo}) creado')
            else:
                self.stdout.write(f'  - Producto "{producto.marca} {producto.modelo}" ya existe')
        
        return productos
    
    def crear_inventarios_iniciales(self, sucursales, productos):
        """Crear inventarios iniciales para las sucursales"""
        import random
        
        # Solo crear inventarios en puntos de venta y bodegas
        sucursales_con_inventario = [s for s in sucursales.values() 
                                   if hasattr(s, 'tipo_sucursal') and 
                                   s.tipo_sucursal in ['punto_venta', 'bodega']]
        
        for sucursal in sucursales_con_inventario:
            for producto in productos:
                cantidad_inicial = random.randint(5, 50)
                stock_minimo = random.randint(3, 10)
                
                inventario, created = Inventario.objects.get_or_create(
                    sucursal=sucursal,
                    producto=producto,
                    defaults={
                        'cantidad': cantidad_inicial,
                        'stock_minimo': stock_minimo
                    }
                )
                
                if created:
                    self.stdout.write(f'  + Inventario {producto.codigo} en {sucursal.nombre}: {cantidad_inicial} unidades')
    
    def crear_traslados_ejemplo(self, sucursales, productos, usuarios):
        """Crear algunos traslados de ejemplo"""
        if len(productos) < 2:
            return
        
        # Traslado pendiente de Guayaquil a Quito
        producto1 = productos[0]
        traslado1 = Traslado.objects.create(
            producto=producto1,
            sucursal_origen=sucursales[1],  # Guayaquil
            sucursal_destino=sucursales[2],  # Quito
            cantidad_entregada=5,
            cantidad_recibida=0,
            estado='pendiente',
            usuario=usuarios[3],  # ninefifteen_guayaquil
            tipo_documento='guia_remision',
            documento_respaldo='GR-001-2024'
        )
        self.stdout.write(f'  + Traslado pendiente creado: {producto1.codigo} de Guayaquil a Quito')
        
        # Traslado confirmado de Cuenca a Laboratorio Guayaquil
        producto2 = productos[1]
        traslado2 = Traslado.objects.create(
            producto=producto2,
            sucursal_origen=sucursales[3],  # Cuenca
            sucursal_destino=sucursales[4],  # Lab Guayaquil
            cantidad_entregada=3,
            cantidad_recibida=3,
            estado='confirmado',
            usuario=usuarios[5],  # ninefifteen_cuenca
            tipo_documento='orden_trabajo',
            documento_respaldo='OT-002-2024'
        )
        self.stdout.write(f'  + Traslado confirmado creado: {producto2.codigo} de Cuenca a Lab Guayaquil')
        
        # Crear algunos movimientos de inventario de ejemplo
        now = timezone.now()
        
        # Entrada de inventario
        MovimientoInventario.objects.create(
            sucursal=sucursales[1],  # Guayaquil
            producto=productos[0],
            tipo_movimiento='entrada',
            tipo_documento='factura',
            cantidad=20,
            fecha=now - timedelta(days=5),
            comentario='COMPRA INICIAL DE MERCADERÍA',
            documento_respaldo='FAC-001-2024',
            usuario=usuarios[3]
        )
        
        # Salida de inventario
        MovimientoInventario.objects.create(
            sucursal=sucursales[1],  # Guayaquil
            producto=productos[0],
            tipo_movimiento='salida',
            tipo_documento='nota_venta',
            cantidad=2,
            fecha=now - timedelta(days=2),
            comentario='VENTA AL POR MENOR',
            documento_respaldo='NV-001-2024',
            usuario=usuarios[3]
        )
        
        self.stdout.write('  + Movimientos de inventario de ejemplo creados')