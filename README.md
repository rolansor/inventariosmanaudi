# Sistema de Inventarios Manaudi

Aplicación web para el control de inventarios de los clientes de **MANAUDI S.A.**
Permite administrar varias empresas de forma aislada, cada una con sus sucursales,
catálogo de productos, stock por sucursal, movimientos (entradas/salidas), traslados
entre sucursales y reportes.

| Componente | Tecnología |
|---|---|
| Backend | Python 3.10 · Django 4.2 LTS |
| Base de datos | MySQL 8 (driver PyMySQL) |
| Frontend | Plantillas Django · Bootstrap 5 (tema Color Admin) · jQuery · DataTables · Select2 |
| Ejecución local | Docker Compose (`web` + `db`) |
| Producción | PythonAnywhere (`sifcol.pythonanywhere.com`) |

## Documentación

Los manuales (usuario y técnico), el guion de demostración, el documento Word/PDF, las capturas y
los videos del recorrido se entregan por separado, fuera de este repositorio. En el código quedan:

| Documento | Para quién | Contenido |
|---|---|---|
| [docker/dumps/README.md](docker/dumps/README.md) | Desarrolladores | Importar/exportar la base de datos del contenedor |
| [CLAUDE.md](CLAUDE.md) | Asistentes de IA | Resumen técnico para trabajar con el código |

El código Python está documentado con docstrings en módulos, modelos, vistas y formularios.

## Puesta en marcha (desarrollo)

Requisitos: Docker Desktop. No se necesita Python ni MySQL instalados en la máquina.

```bash
git clone <repositorio> inventariosmanaudi
cd inventariosmanaudi
cp .env.example .env          # ajustar si hace falta (puertos, claves)
docker compose up -d          # construye la imagen, levanta MySQL y Django
docker compose logs -f web    # esperar "Starting development server"
```

- Aplicación: <http://127.0.0.1:8012>
- Admin de Django: <http://127.0.0.1:8012/admin/>
- MySQL: `127.0.0.1:3307` (usuario `root`, clave `f4d3s2a1`, base `inv_manaudi`)

El contenedor `web` ejecuta `migrate` al arrancar. La primera vez la base está vacía:
cargar los datos de prueba (siguiente sección) o importar un dump real
(ver `docker/dumps/README.md`).

## Datos de prueba

```bash
# 1) Estructura: grupos, 3 empresas, 9 sucursales, 13 usuarios, catálogo y stock inicial
docker compose exec web python manage.py populate_data

# 2) Historial de demostración: 30 días de movimientos, traslados pendientes y
#    confirmados, alertas de stock bajo, un producto agotado y otro inactivo
docker compose exec web python manage.py populate_demo
```

Todas las contraseñas son **1234**. Usuarios de la empresa *TechCorp Ecuador*
(las otras dos empresas siguen el mismo patrón con los prefijos `comercia_` y `distribu_`):

| Usuario | Rol (grupos) | Sucursal | Puede… |
|---|---|---|---|
| `admin` | Superusuario (todos los grupos) | — | Todo, y cambiar de empresa desde la barra superior |
| `techcorp_manaudi` | Manaudi + Supervisor + Encargado + Auditor | — | Administrar empresas/sucursales, eliminar clasificación, activar/desactivar productos, carga masiva |
| `techcorp_supervisor` | Supervisor + Encargado + Auditor | Matriz Quito | Clasificación, productos, movimientos, traslados, consultas y reportes |
| `techcorp_encargado` | Encargado | Sucursal Guayaquil | Entradas/salidas y traslados de su sucursal, confirmar recepciones |
| `techcorp_auditor` | Auditor | — | Solo lectura: lista de productos y reportes |

Para volver a empezar: `docker compose exec web python manage.py populate_data --clear`
(conserva los superusuarios) y luego `populate_demo`.

## Comandos útiles

```bash
docker compose up -d                               # levantar
docker compose down                                # detener (conserva la base de datos)
docker compose down -v                             # detener y BORRAR la base de datos
docker compose build && docker compose up -d       # tras cambiar requirements.txt
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell

# Respaldo / restauración de la base del contenedor
docker compose exec db mysqldump -uroot -pf4d3s2a1 inv_manaudi > docker/dumps/backup.sql
docker compose exec -T db mysql -uroot -pf4d3s2a1 inv_manaudi < docker/dumps/backup.sql
```

## Estructura del repositorio

```
.
├── docker-compose.yml, Dockerfile, docker/   # contenedores (entrypoint espera a MySQL y migra)
├── .env.example                              # variables de entorno
├── requirements.txt
└── inv_manaudi/                              # proyecto Django (manage.py)
    ├── inv_manaudi/      settings.py, urls.py
    ├── usuarios/         empresas, sucursales, usuarios/perfiles, login, dashboard, permisos
    ├── categorias/       Categoría > Subcategoría > Clase
    ├── productos/        catálogo de productos
    ├── inventario/       stock por sucursal, movimientos, traslados
    ├── reportes/         reporte diario, inventario valorizado, carga masiva Excel
    ├── templates/        base.html (layout, menú lateral)
    └── static/           Bootstrap, DataTables, Select2, FontAwesome…
```

## Roles y permisos (resumen)

| Funcionalidad | Manaudi | Supervisor | Encargado | Auditor |
|---|:-:|:-:|:-:|:-:|
| Empresas y sucursales | ✅ | | | |
| Clasificación: crear / editar | ✅ | ✅ | | |
| Clasificación: eliminar | ✅ | | | |
| Productos: crear / editar | ✅ | ✅ | | |
| Productos: activar / desactivar | ✅ | | | |
| Productos: lista completa (DataTables) | ✅ | ✅ | | ✅ |
| Productos: búsqueda | ✅ | ✅ | ✅ | |
| Entradas / salidas, traslados, acuse de recibo | ✅ | ✅ | ✅ | |
| Movimientos por producto | ✅ | ✅ | ✅ | |
| Movimientos por empresa / sucursal | ✅ | ✅ | | |
| Reportes | ✅ | ✅ | | ✅ |
| Carga masiva de productos | ✅ | | | |

Los permisos se resuelven por **grupo** (uno por vista); no hay herencia. La tabla refleja
los grupos que asigna `populate_data` (Manaudi tiene los cuatro, Supervisor tiene tres).
La gestión de usuarios se hace desde el admin de Django.

## Producción

Definir en el entorno `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`,
`DJANGO_CSRF_TRUSTED_ORIGINS` y las variables `DB_*` (ver `.env.example`). Detalles de
despliegue y mantenimiento en el manual técnico (entregado por separado).
