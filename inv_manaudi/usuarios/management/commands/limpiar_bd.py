from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction
from usuarios.models import Usuario, Empresa, Sucursal, UsuarioPerfil
from productos.models import Producto
from inventario.models import Traslado, MovimientoInventario, Inventario


class Command(BaseCommand):
    help = 'Limpiar la base de datos eliminando todos los datos de usuario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma que quieres eliminar todos los datos',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING('ADVERTENCIA: Este comando eliminará TODOS los datos de la base de datos.')
            )
            self.stdout.write(
                self.style.WARNING('Para confirmar, ejecuta: python manage.py limpiar_bd --confirm')
            )
            return

        with transaction.atomic():
            self.stdout.write('Iniciando limpieza de base de datos...')
            
            # Eliminar en orden para evitar problemas de foreign keys
            self.stdout.write('Eliminando movimientos de inventario...')
            count = MovimientoInventario.objects.count()
            MovimientoInventario.objects.all().delete()
            self.stdout.write(f'  - {count} movimientos eliminados')
            
            self.stdout.write('Eliminando traslados...')
            count = Traslado.objects.count()
            Traslado.objects.all().delete()
            self.stdout.write(f'  - {count} traslados eliminados')
            
            self.stdout.write('Eliminando inventarios...')
            count = Inventario.objects.count()
            Inventario.objects.all().delete()
            self.stdout.write(f'  - {count} inventarios eliminados')
            
            self.stdout.write('Eliminando productos...')
            count = Producto.objects.count()
            Producto.objects.all().delete()
            self.stdout.write(f'  - {count} productos eliminados')
            
            self.stdout.write('Eliminando perfiles de usuario...')
            count = UsuarioPerfil.objects.count()
            UsuarioPerfil.objects.all().delete()
            self.stdout.write(f'  - {count} perfiles eliminados')
            
            self.stdout.write('Eliminando usuarios...')
            count = Usuario.objects.count()
            Usuario.objects.all().delete()
            self.stdout.write(f'  - {count} usuarios eliminados')
            
            self.stdout.write('Eliminando sucursales...')
            count = Sucursal.objects.count()
            Sucursal.objects.all().delete()
            self.stdout.write(f'  - {count} sucursales eliminadas')
            
            self.stdout.write('Eliminando empresas...')
            count = Empresa.objects.count()
            Empresa.objects.all().delete()
            self.stdout.write(f'  - {count} empresas eliminadas')
            
            self.stdout.write('Eliminando grupos...')
            count = Group.objects.count()
            Group.objects.all().delete()
            self.stdout.write(f'  - {count} grupos eliminados')
            
            self.stdout.write(self.style.SUCCESS('+ Base de datos limpiada exitosamente!'))
            self.stdout.write(self.style.SUCCESS('Ahora puedes ejecutar: python manage.py poblar_bd'))