# Sistema de Inventarios Manaudi - Documentación para Claude

## 🏗️ Arquitectura del Proyecto

### Stack Tecnológico
- **Framework**: Django 4.2.30 (LTS)
- **Base de Datos**: MySQL 8 (PyMySQL)
- **Frontend**: Templates Django con Bootstrap 5 (tema Color Admin), DataTables, Select2
- **Autenticación**: Sistema customizado con modelo Usuario personalizado
- **Entorno de ejecución**: Docker (`docker compose up -d`). No se usa entorno virtual local.

## 📁 Estructura del Proyecto

```
inv_manaudi/
├── usuarios/        # Gestión de usuarios, empresas y sucursales
├── inventario/      # Control de inventarios y movimientos
├── productos/       # Administración de productos
├── categorias/      # Categorías y subcategorías
├── reportes/        # Generación de reportes
└── templates/       # Templates base
```

## 🗄️ Modelos de Datos Principales

### usuarios/models.py
- **Empresa**: Entidad principal del sistema multi-empresa
- **Sucursal**: Incluye tipos (bodega, punto_venta, laboratorio)
- **Usuario**: Extiende AbstractUser con campos adicionales
- **UsuarioPerfil**: Relaciona usuario con empresa y sucursal

### productos/models.py
- **Producto**: 
  - Campos clave: codigo, nombre, precio, tipo_producto (unidad/juego)
  - Estado: activo/inactivo
  - Constraint único: codigo + empresa
  - Manager personalizado para filtrar por empresa

### inventario/models.py
- **Inventario**: 
  - Stock actual por producto/sucursal
  - Incluye stock_minimo para alertas
  - Métodos: is_stock_bajo(), valor_inventario()
  
- **MovimientoInventario**:
  - Tipos: entrada/salida
  - Documentos: nota_venta, factura, orden_trabajo, etc.
  - Auto-actualiza inventario al guardar
  
- **Traslado**:
  - Estados: pendiente/confirmado
  - Crea automáticamente movimientos de entrada/salida
  - Validaciones de stock y sucursales

### categorias/models.py
- **Categoria**: Por empresa, nombre en mayúsculas automático
- **Subcategoria**: Relacionada a categoría, nombre en mayúsculas

## 🔐 Sistema de Permisos

### Decorador @control_acceso
- Verifica permisos basados en grupo del usuario
- Ubicado en: usuarios/templatetags/tags.py

### Grupos (django.contrib.auth.Group)
Los permisos se resuelven por pertenencia a grupo. Un usuario con varios grupos acumula permisos;
`populate_data` asigna a Manaudi todos los grupos y a Supervisor los grupos Supervisor + Encargado + Auditor.

- **Manaudi**: administración (empresas, sucursales, eliminar categorías/subcategorías/clases, activar/desactivar productos, carga masiva).
- **Supervisor**: categorías/subcategorías/clases (crear, editar, listar), productos (crear, editar), movimientos por empresa y sucursal.
- **Encargado**: movimientos de inventario, traslados (iniciar, pendientes, confirmar), búsqueda de productos, movimientos por producto.
- **Auditor**: solo lectura: lista de productos, reportes.

Reglas de `control_acceso`: usuario anónimo → redirige al login con `?next=`; usuario sin el grupo → `acceso_denegado.html` con HTTP 403.

Confirmación de traslados: un usuario **con** sucursal solo confirma traslados destinados a su sucursal;
un usuario **sin** sucursal (Manaudi, superusuario) puede confirmar cualquier traslado de su empresa.

La matriz detallada está más abajo en "Matriz de Permisos por Rol".

## 🌐 URLs y Endpoints Principales

### /usuarios/
- login/, logout/
- empresas/, empresas/editar/<pk>/, empresas/eliminar/<pk>/ (AJAX)
- empresas/<pk>/sucursales, sucursales/editar/<pk>/, sucursales/eliminar/<pk>/ (AJAX)
- cambiar-empresa/<id>/ (solo superusuario: cambia la empresa activa en sesión)

### /inventario/
- movimiento_inventario/
- traslado/iniciar/, traslados_pendientes/, traslado/confirmar/<pk>/
- producto_movimientos/, empresa_movimientos/, sucursal_movimientos/

### /productos/
- nuevo/, lista_productos/ (DataTables server-side), busqueda/, editar/<pk>/
- desactivar/<pk>/, activar/<pk>/ (solo POST)
- bsq_por_codigo/, obtener_modelos/ (JSON)

### /categorias/
- nueva_categoria/ (POST), lista_categorias/, editar/<pk>/, eliminar/<pk>/
- <pk>/nueva_subcategoria/ (POST), <pk>/lista_subcategorias/, subcategorias/editar/<pk>/, subcategorias/eliminar/<pk>/
- subcategorias/<pk>/nueva_clase/ (POST), subcategorias/<pk>/lista_clases/, clases/editar/<pk>/, clases/eliminar/<pk>/
- Todas las vistas filtran por la empresa activa (`obtener_empresa`); un ID de otra empresa devuelve 404.

### /reportes/
- reporte_diario/, inventario_valorizado/
- carga_masiva/, descargar_plantilla/ (Excel; crea categorías/subcategorías/clases nuevas generando códigos de 3 caracteres)

## ⚙️ Configuración Importante (settings.py)

### Variables de entorno (ver `.env.example`)
`settings.py` lee `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`,
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. Sin variables usa los valores locales originales
(root/f4d3s2a1 en localhost:3306, DEBUG=True). ⚠️ En producción definir todas en el entorno.

### Base de Datos
- **Docker**: servicio `db` (MySQL 8.0), expuesto en 127.0.0.1:3307. Volumen `db_data`.
- **Producción**: PythonAnywhere (`sifcol$inv_manaudi`).
- Dumps `.sql` en `docker/dumps/` se importan al crear el volumen por primera vez.

### Configuración Regional
- **LANGUAGE_CODE**: 'es-ec'
- **TIME_ZONE**: 'America/Guayaquil'

### Archivos Estáticos y Media
- STATIC_URL: '/static/'
- MEDIA_URL: '/media/'
- Archivos de soporte se guardan en 'documento_soporte/'

## 🔄 Flujo de Trabajo Principal

### Movimientos de Inventario
1. Usuario registra entrada/salida con documento respaldo
2. Sistema actualiza automáticamente el inventario
3. Valida stock disponible para salidas

### Traslados entre Sucursales
1. Supervisor inicia traslado (crea movimiento de salida)
2. Traslado queda en estado "pendiente"
3. Encargado destino confirma recepción (crea movimiento de entrada)
4. Estado cambia a "confirmado"

### Multi-Empresa
- Cada usuario tiene perfil con empresa asignada
- Productos y movimientos filtrados por empresa
- Códigos de producto únicos por empresa

## 📊 Características Especiales

### Sistema Multi-Empresa
- Aislamiento completo de datos por empresa
- Usuarios pueden pertenecer a una empresa y sucursal específica

### Control de Stock
- Alertas de stock bajo (stock_minimo)
- Validación automática en salidas
- Cálculo de valor de inventario

### Trazabilidad
- Registro de usuario en cada movimiento
- Documentos de respaldo adjuntables
- Historial completo de movimientos

## 🚨 Puntos de Atención

### Seguridad
- Los valores por defecto de SECRET_KEY, DEBUG y credenciales de BD en settings.py son de desarrollo;
  en producción deben definirse por variables de entorno.

### Migraciones
- Las migraciones se borraron del repo en agosto de 2025 y se regeneraron el 18/10/2026
  con los mismos nombres (`0001_initial`, `0002_initial`, `0003_initial`, `0002_traslado_producto`).
- El contenedor `web` ejecuta `migrate` al arrancar (desactivable con `RUN_MIGRATIONS=0`).

### Validaciones Críticas
- Stock insuficiente en salidas
- Sucursales de misma empresa en traslados
- Cantidad recibida en confirmación de traslados

## 📝 Notas de Desarrollo

### Helpers Importantes
- `obtener_empresa(request)` (usuarios/views.py): empresa del usuario; para superusuario, la elegida en sesión
- `control_acceso` (usuarios/templatetags/tags.py): decorador de permisos por grupo
- `es_ajax(request)` (usuarios/utils.py): reemplazo de `request.is_ajax()` (eliminado en Django 4)
- `Producto.objects.para_empresa(empresa)`: manager para filtrar por empresa
- Integridad de stock: `MovimientoInventario.save()` y `Traslado.save()/confirmar()` corren en
  `transaction.atomic()` con `select_for_update()` sobre la fila de inventario

### Plantillas Base
- base.html: Template principal con Bootstrap 5
- DataTables integrado para listados
- Select2 para selectores mejorados

### Assets
- Bootstrap 5 + FontAwesome
- jQuery + DataTables
- Plugins: Select2, Bootstrap Datepicker, PDFMake

## 🔧 Comandos Útiles (Docker)

```bash
# Levantar todo (web: http://127.0.0.1:8012, MySQL: 127.0.0.1:3307)
docker compose up -d
docker compose logs -f web

# Reconstruir la imagen tras cambiar requirements.txt
docker compose build && docker compose up -d

# Comandos de Django (siempre dentro del contenedor)
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py check

# Poblar base de datos con datos de prueba
docker compose exec web python manage.py populate_data                  # Crea datos de prueba
docker compose exec web python manage.py populate_data --clear          # Limpia y recrea todos los datos
docker compose exec web python manage.py populate_data --empresas 2     # Crea solo 2 empresas

# Exportar / importar la base del contenedor
docker compose exec db mysqldump -uroot -pf4d3s2a1 inv_manaudi > docker/dumps/backup.sql
docker compose exec -T db mysql -uroot -pf4d3s2a1 inv_manaudi < docker/dumps/backup.sql
```



## 👥 Usuarios del Sistema

### Comando populate_data
El comando `python manage.py populate_data` crea automáticamente usuarios de prueba con la siguiente estructura:

**NOTA**: Todas las contraseñas son: **1234**

### Usuarios Creados por Empresa

#### TechCorp Ecuador
| Usuario                 | Nombre              | Rol           | Sucursal           | Email                   | Grupos                                  |
|-------------------------|---------------------|---------------|--------------------|-------------------------|-----------------------------------------|
| **admin**               | Super Admin         | Superusuario  | -                  | admin@sistema.com       | Todos                                   |
| **techcorp_manaudi**    | Manaudi TechCorp    | Manaudi       | -                  | manaudi@techcorp.com    | Manaudi, Supervisor, Encargado, Auditor |
| **techcorp_supervisor** | Supervisor TechCorp | Supervisor    | Matriz Quito       | supervisor@techcorp.com | Supervisor, Encargado                   |
| **techcorp_encargado**  | Encargado TechCorp  | Encargado     | Sucursal Guayaquil | encargado@techcorp.com  | Encargado                               |
| **techcorp_auditor**    | Auditor TechCorp    | Auditor       | -                  | auditor@techcorp.com    | Auditor                                 |

#### Comercial Andina
| Usuario                 | Nombre               | Rol           | Sucursal          | Email                   | Grupos                                  |
|-------------------------|----------------------|---------------|-------------------|-------------------------|-----------------------------------------|
| **comercia_manaudi**    | Manaudi Comercial    | Manaudi       | -                 | manaudi@comercia.com    | Manaudi, Supervisor, Encargado, Auditor |
| **comercia_supervisor** | Supervisor Comercial | Supervisor    | Bodega Principal  | supervisor@comercia.com | Supervisor, Encargado                   |
| **comercia_encargado**  | Encargado Comercial  | Encargado     | Punto Venta Norte | encargado@comercia.com  | Encargado                               |
| **comercia_auditor**    | Auditor Comercial    | Auditor       | -                 | auditor@comercia.com    | Auditor                                 |

#### Distribuidora Nacional
| Usuario                 | Nombre                   | Rol           | Sucursal            | Email                   | Grupos                                  |
|-------------------------|--------------------------|---------------|---------------------|-------------------------|-----------------------------------------|
| **distribu_manaudi**    | Manaudi Distribuidora    | Manaudi       | -                   | manaudi@distribu.com    | Manaudi, Supervisor, Encargado, Auditor |
| **distribu_supervisor** | Supervisor Distribuidora | Supervisor    | Centro Distribución | supervisor@distribu.com | Supervisor, Encargado                   |
| **distribu_encargado**  | Encargado Distribuidora  | Encargado     | Tienda Cuenca       | encargado@distribu.com  | Encargado                               |
| **distribu_auditor**    | Auditor Distribuidora    | Auditor       | -                   | auditor@distribu.com    | Auditor                                 |

### Estructura de Empresas y Sucursales

#### TechCorp Ecuador
- **Matriz Quito** (Bodega) - UIO
- **Sucursal Guayaquil** (Punto de Venta) - GYE  
- **Laboratorio Quito** (Laboratorio) - LAB

#### Comercial Andina
- **Bodega Principal** (Bodega) - BOD
- **Punto Venta Norte** (Punto de Venta) - PVN
- **Punto Venta Sur** (Punto de Venta) - PVS

#### Distribuidora Nacional
- **Centro Distribución** (Bodega) - CDI
- **Tienda Cuenca** (Punto de Venta) - CUE
- **Tienda Loja** (Punto de Venta) - LOJ

### Datos de Prueba Incluidos
El comando también crea:
- **Categorías**: Electrónica, Oficina
- **Subcategorías**: Computadoras, Celulares, Papelería, Mobiliario
- **Clases**: Laptops, Desktops, Tablets, Smartphones, etc.
- **Productos**: 10 productos por empresa con códigos únicos
- **Inventario**: Stock inicial aleatorio (10-100 unidades)
- **Movimientos**: Entradas y salidas de ejemplo

### Comandos de Gestión
```bash
# Crear datos de prueba completos
python manage.py populate_data

# Limpiar y recrear todos los datos
python manage.py populate_data --clear

# Crear solo 1 empresa (en lugar de las 3 por defecto)
python manage.py populate_data --empresas 1
```

## 🏢 Estructura Organizacional y Permisos

### Diagrama de Jerarquía Multi-Empresa
```
                        ┌──────────────────────────────────────┐
                        │            SUPERUSUARIO              │
                        │         admin (Super Admin)         │
                        │         Permisos: GLOBALES          │
                        └─────────────────┬────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼──────────┐            ┌────────▼─────────┐            ┌──────────▼────────┐
│   TECHCORP       │            │  COMERCIAL       │            │   DISTRIBUIDORA   │
│   ECUADOR        │            │    ANDINA        │            │    NACIONAL       │
└─────────┬────────┘            └─────────┬────────┘            └──────────┬────────┘
          │                               │                               │
    ┌─────▼─────┐                   ┌─────▼─────┐                   ┌─────▼─────┐
    │  MANAUDI  │                   │  MANAUDI  │                   │  MANAUDI  │
    │ techcorp_ │                   │ comercia_ │                   │ distribu_ │
    │  manaudi  │                   │  manaudi  │                   │  manaudi  │
    └─────┬─────┘                   └─────┬─────┘                   └─────┬─────┘
          │                               │                               │
  ┌───────▼───────┐               ┌───────▼───────┐               ┌───────▼───────┐
  │  SUPERVISOR   │               │  SUPERVISOR   │               │  SUPERVISOR   │
  │ techcorp_     │               │ comercia_     │               │ distribu_     │
  │ supervisor    │               │ supervisor    │               │ supervisor    │
  │ (Matriz UIO)  │               │ (Bodega BOD)  │               │ (Centro CDI)  │
  └───────┬───────┘               └───────┬───────┘               └───────┬───────┘
          │                               │                               │
  ┌───────▼───────┐               ┌───────▼───────┐               ┌───────▼───────┐
  │  ENCARGADO    │               │  ENCARGADO    │               │  ENCARGADO    │
  │ techcorp_     │               │ comercia_     │               │ distribu_     │
  │ encargado     │               │ encargado     │               │ encargado     │
  │ (Sucursal GYE)│               │ (P.Venta PVN) │               │ (Tienda CUE)  │
  └───────┬───────┘               └───────┬───────┘               └───────┬───────┘
          │                               │                               │
  ┌───────▼───────┐               ┌───────▼───────┐               ┌───────▼───────┐
  │   AUDITOR     │               │   AUDITOR     │               │   AUDITOR     │
  │ techcorp_     │               │ comercia_     │               │ distribu_     │
  │   auditor     │               │   auditor     │               │   auditor     │
  │ (Solo lectura)│               │ (Solo lectura)│               │ (Solo lectura)│
  └───────────────┘               └───────────────┘               └───────────────┘

SUCURSALES POR EMPRESA:
──────────────────────

TechCorp Ecuador:           Comercial Andina:           Distribuidora Nacional:
• Matriz Quito (UIO)        • Bodega Principal (BOD)    • Centro Distribución (CDI)
• Sucursal Guayaquil (GYE)  • Punto Venta Norte (PVN)   • Tienda Cuenca (CUE)
• Laboratorio Quito (LAB)   • Punto Venta Sur (PVS)     • Tienda Loja (LOJ)
```

### Matriz de Permisos por Rol

| Funcionalidad                 | Manaudi | Supervisor | Encargado | Auditor |
|-------------------------------|:-------:|:----------:|:---------:|:-------:|
| **Gestión de Empresas**       |    ✅    |     ❌      |     ❌     |    ❌    |
| **Gestión de Sucursales**     |    ✅    |     ❌      |     ❌     |    ❌    |
| **Gestión de Usuarios**       |    ✅    |     ❌      |     ❌     |    ❌    |
| **Categorías - Crear/Editar** |    ✅    |     ✅      |     ❌     |    ❌    |
| **Categorías - Eliminar**     |    ✅    |     ❌      |     ❌     |    ❌    |
| **Productos - Crear/Editar**  |    ✅    |     ✅      |     ❌     |    ❌    |
| **Productos - Eliminar**      |    ✅    |     ❌      |     ❌     |    ❌    |
| **Productos - Listar**        |    ✅    |     ✅      |     ❌     |    ✅    |
| **Productos - Buscar**        |    ✅    |     ✅      |     ✅     |    ❌    |
| **Iniciar Traslados**         |    ✅    |     ✅      |     ✅     |    ❌    |
| **Confirmar Traslados**       |    ✅    |     ✅      |     ✅     |    ❌    |
| **Movimientos Inventario**    |    ✅    |     ✅      |     ✅     |    ❌    |
| **Reportes**                  |    ✅    |     ✅      |     ❌     |    ✅    |

### Flujo de Trabajo Multi-Empresa

#### TechCorp Ecuador
```
┌─────────────────────────────────────────────────────────────┐
│                    MATRIZ QUITO (UIO)                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Supervisor: techcorp_supervisor                    │     │
│  │ Funciones Centrales:                               │     │
│  │ • Gestión de productos y categorías                │     │
│  │ • Coordinación de traslados                        │     │
│  │ • Generación de reportes                           │     │
│  │ • Control de inventario principal                  │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
┌───────────────▼───┐  ┌──────▼──────┐  ┌───▼────────────┐
│ SUCURSAL GYE (GYE)│  │LAB UIO (LAB)│  │  TRASLADOS     │
│                   │  │             │  │  INTER-        │
│ Encargado:        │  │ Personal:   │  │  SUCURSALES    │
│ techcorp_encargado│  │ Técnicos    │  │                │
│                   │  │ Lab         │  │ • GYE ↔ UIO    │
│ Funciones:        │  │             │  │ • LAB ↔ UIO    │
│ • Ventas          │  │ Funciones:  │  │ • GYE ↔ LAB    │
│ • Atención cliente│  │ • Análisis  │  │                │
│ • Stock local     │  │ • Pruebas   │  │ Estados:       │
│ • Recepción       │  │ • R&D       │  │ • Pendiente    │
│                   │  │ • QC        │  │ • Confirmado   │
└───────────────────┘  └─────────────┘  └────────────────┘
```

#### Comercial Andina
```
┌─────────────────────────────────────────────────────────────┐
│                 BODEGA PRINCIPAL (BOD)                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Supervisor: comercia_supervisor                    │     │
│  │ Funciones de Distribución:                         │     │
│  │ • Control de stock central                         │     │
│  │ • Coordinación logística                           │     │
│  │ • Distribución a puntos de venta                   │     │
│  │ • Recepción de mercancía                           │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
┌───────────────▼───┐              ┌────────▼────────┐
│P.VENTA NORTE (PVN)│              │P.VENTA SUR (PVS)│
│                   │              │                 │
│Encargado:         │              │ Personal:       │
│comercia_encargado │              │ Vendedores      │
│                   │              │                 │
│Funciones:         │              │ Funciones:      │
│• Ventas al público│              │ • Ventas        │
│• Atención cliente │              │ • Inventario    │
│• Manejo de caja   │              │ • Exhibición    │
│• Inventario PV    │              │ • Recepción     │
│• Reportes ventas  │              │                 │
└───────────────────┘              └─────────────────┘
```

#### Distribuidora Nacional
```
┌─────────────────────────────────────────────────────────────┐
│              CENTRO DISTRIBUCIÓN (CDI)                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Supervisor: distribu_supervisor                    │     │
│  │ Funciones de Distribución Nacional:                │     │
│  │ • Logística nacional                               │     │
│  │ • Control de inventario central                    │     │
│  │ • Coordinación inter-ciudades                      │     │
│  │ • Planificación de distribución                    │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
┌───────────────▼───┐              ┌────────▼────────┐
│TIENDA CUENCA (CUE)│              │TIENDA LOJA (LOJ)│
│                   │              │                 │
│Encargado:         │              │ Personal:       │
│distribu_encargado │              │ Vendedores      │
│                   │              │ locales         │
│Funciones:         │              │                 │
│• Ventas locales   │              │ Funciones:      │
│• Stock regional   │              │ • Ventas        │
│• Atención cliente │              │ • Inventario    │
│• Recepción        │              │ • Atención      │
│• Reportes zona    │              │ • Recepción     │
└───────────────────┘              └─────────────────┘
```

### Reglas de Negocio y Restricciones

1. **Aislamiento por Empresa**: Cada usuario solo ve datos de su empresa asignada
2. **Traslados**: Solo entre sucursales de la misma empresa
3. **Jerarquía de Permisos**: Un rol superior tiene todos los permisos de los roles inferiores
4. **Stock Mínimo**: Alertas automáticas cuando el inventario está por debajo del mínimo
5. **Documentación**: Todos los movimientos requieren documento de respaldo

## 📌 TODOs y Mejoras Sugeridas

1. **Seguridad**: definir SECRET_KEY, DEBUG=0 y credenciales por entorno en producción
2. **Producción**: verificar la versión de Python de PythonAnywhere (Django 4.2 requiere 3.8+)
3. **Tests**: Agregar pruebas unitarias y de integración
4. **API REST**: Considerar agregar Django REST Framework
5. **Documentación**: Agregar docstrings en vistas y modelos
6. **Logs**: Implementar sistema de logging
7. **Backups**: Configurar respaldos automáticos de BD