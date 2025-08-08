# Sistema de Gestión de Inventarios Manaudi

## Descripción del Proyecto
Sistema web de gestión de inventarios multi-empresa desarrollado en Django 3.2.25 para empresas con múltiples sucursales. Permite control de inventario, movimientos entre sucursales, gestión de productos y reportería.

## Información Técnica

### Stack Tecnológico
- **Framework**: Django 3.2.25
- **Base de Datos**: MySQL (via PyMySQL)
- **Frontend**: Bootstrap 5, jQuery, DataTables
- **Python**: Compatible con Python 3.x
- **Servidor**: Configurado para PythonAnywhere y desarrollo local

### Dependencias Principales
```txt
Django==3.2.25
PyMySQL==1.1.1
beautifulsoup4==4.12.3
lxml==5.3.0
requests==2.31.0
```

## Estructura del Proyecto

```
inventariosmanaudi/
├── inv_manaudi/           # Directorio principal del proyecto
│   ├── inv_manaudi/       # Configuración principal
│   │   ├── settings.py    # Configuraciones Django
│   │   ├── urls.py        # URLs principales
│   │   └── wsgi.py        # Configuración WSGI
│   ├── usuarios/          # App de gestión de usuarios
│   ├── inventario/        # App de control de inventario
│   ├── categorias/        # App de categorías de productos
│   ├── productos/         # App de gestión de productos
│   ├── auxiliares/        # App de servicios auxiliares (SRI)
│   ├── reportes/          # App de reportería
│   ├── templates/         # Templates base
│   ├── static/            # Archivos estáticos
│   └── media/             # Archivos subidos
├── manage.py              # Script de gestión Django
├── requirements.txt       # Dependencias del proyecto
└── venv/                  # Entorno virtual
```

## Modelos de Datos

### usuarios/models.py
- **Empresa**: Entidad principal multi-tenant
- **Sucursal**: Ubicaciones/sucursales (bodega, punto_venta, laboratorio)
- **Usuario**: Usuario personalizado extendiendo AbstractUser
- **UsuarioPerfil**: Perfil vinculando usuario con empresa y sucursal

### inventario/models.py
- **Inventario**: Stock actual por sucursal y producto
- **MovimientoInventario**: Registro de entradas/salidas
- **Traslado**: Transferencias entre sucursales con workflow de confirmación

### categorias/models.py
- **Categoria**: Categorías principales por empresa
- **Subcategoria**: Subcategorías dentro de categorías

### productos/models.py
- **Producto**: Productos ópticos con código generado automáticamente
- **ProductoManager**: Manager personalizado para filtrado por empresa
- **Campos ópticos**: linea, sublinea, clase, material, marca, modelo
- **Generación de código**: Combinación automática de linea+sublinea+clase

## Funcionalidades Principales

### 1. Gestión de Usuarios y Acceso
- Sistema de autenticación personalizado
- Roles: Administrador, Supervisor, Encargado, Manaudi
- Control de acceso basado en grupos Django
- Usuarios asignados a empresas y sucursales específicas

### 2. Control de Inventario
- Registro de entradas y salidas
- Control de stock mínimo con alertas
- Movimientos con documentación de soporte
- Actualización automática de inventarios

### 3. Sistema de Traslados
- Transferencias entre sucursales
- Workflow de confirmación (pendiente → confirmado)
- Traslados especiales para laboratorio
- Generación automática de movimientos

### 4. Gestión de Productos Ópticos
- CRUD completo de productos especializados en óptica
- Generación automática de códigos (Línea + Sublínea + Clase)
- Campos específicos: marca, modelo, material, línea, sublínea, clase
- Estados: activo/inactivo
- Búsqueda por filtros de clasificación óptica (línea, sublínea, clase)

### 5. Integración Externa
- Conexión con SRI (Servicio de Rentas Internas de Ecuador)
- Validación de RUC
- Web scraping para información tributaria

### 6. Reportería
- Reporte de movimientos diarios
- Movimientos por empresa/sucursal/producto
- Análisis de inventario por ubicación

## URLs y Endpoints

### Principales
- `/` - Dashboard principal
- `/admin/` - Panel de administración Django
- `/usuarios/` - Gestión de usuarios
- `/inventario/` - Operaciones de inventario
- `/productos/` - Gestión de productos
- `/categorias/` - Gestión de categorías
- `/reportes/` - Módulo de reportes
- `/auxiliares/` - Servicios auxiliares

### APIs Internas
- `/productos/bsq_por_codigo/` - Búsqueda de productos por código (JSON)
- `/productos/busqueda/` - Búsqueda con filtros de clasificación óptica
- `/productos/busqueda_modelo/` - Búsqueda específica por modelo
- `/auxiliares/consulta_id/` - Consulta información tributaria

## Configuración

### Base de Datos
- **Local**: MySQL en localhost:3306
- **Producción**: Configuración para PythonAnywhere comentada
- **Nombre BD**: inv_manaudi

### Archivos Estáticos
- URL: `/static/`
- Directorio: `BASE_DIR/static`
- Incluye: Bootstrap, jQuery, DataTables, FontAwesome

### Archivos Media
- URL: `/media/`
- Directorio: `BASE_DIR/media`
- Almacena: documentos de soporte para movimientos

### Configuración Regional
- **Idioma**: Español Ecuador (es-ec)
- **Zona Horaria**: America/Guayaquil
- **Formato Fechas**: Localizado para Ecuador

## Seguridad y Permisos

### Decoradores de Acceso
- `@login_required`: Requiere autenticación
- `@control_acceso('rol')`: Verifica pertenencia a grupo específico

### Niveles de Acceso
1. **Administrador**: Acceso total al sistema
2. **Supervisor**: Gestión de inventario y reportes
3. **Encargado**: Operaciones básicas de inventario
4. **Manaudi**: Funciones especiales del sistema

### Filtrado de Datos
- Datos automáticamente filtrados por empresa del usuario
- Validación de sucursal en operaciones de inventario
- Aislamiento completo entre empresas

## Comandos de Gestión

### Configuración Inicial (IMPORTANTE: Ejecutar en este orden)

1. **Crear base de datos MySQL** (si no existe):
   ```sql
   CREATE DATABASE inv_manaudi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Instalar dependencias**
3. **Crear y aplicar migraciones**
4. **Poblar base de datos** (opcional, para datos de prueba)

### Windows

#### Opción 1: Activar entorno virtual en CMD
```bash
# Activar entorno virtual
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Cambiar al directorio del proyecto
cd inv_manaudi

# IMPORTANTE: Primero crear las migraciones
python manage.py makemigrations usuarios productos inventario reportes auxiliares

# Aplicar migraciones (esto crea las tablas en la BD)
python manage.py migrate

# SOLO DESPUÉS de las migraciones, poblar con datos de prueba
python manage.py poblar_bd

# Crear superusuario (opcional)
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver

# Recolectar archivos estáticos
python manage.py collectstatic
```

#### Opción 2: Usar PowerShell con rutas directas (sin activar venv)
```powershell
# Instalar dependencias usando el pip del venv
venv\Scripts\pip.exe install -r requirements.txt

# IMPORTANTE: Primero crear migraciones para todas las apps
powershell -Command "venv\Scripts\python.exe inv_manaudi\manage.py makemigrations usuarios productos inventario reportes auxiliares"

# Aplicar migraciones (esto crea las tablas en la BD)
powershell -Command "venv\Scripts\python.exe inv_manaudi\manage.py migrate"

# SOLO DESPUÉS de las migraciones, poblar base de datos
powershell -Command "venv\Scripts\python.exe inv_manaudi\manage.py poblar_bd"

# Limpiar base de datos (usar con precaución)
powershell -Command "venv\Scripts\python.exe inv_manaudi\manage.py limpiar_bd --confirm"

# Crear superusuario
powershell -Command "venv\Scripts\python.exe inv_manaudi\manage.py createsuperuser"

# Ejecutar servidor de desarrollo
powershell -Command "venv\Scripts\python.exe inv_manaudi\manage.py runserver"
```

**Nota importante**: 
- La opción de PowerShell es útil cuando hay problemas con la activación del entorno virtual o cuando se ejecutan comandos desde scripts automatizados
- SIEMPRE ejecutar las migraciones antes de poblar la base de datos, de lo contrario obtendrás errores de tablas no existentes

### Linux/Mac
```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Cambiar al directorio del proyecto
cd inv_manaudi

# Migraciones de base de datos
python manage.py makemigrations
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver

# Recolectar archivos estáticos
python manage.py collectstatic
```

## Población de Base de Datos

### Comandos de Gestión de Datos

El proyecto incluye comandos personalizados para gestionar la población de la base de datos:

#### Limpiar Base de Datos
```bash
# Windows
cd inv_manaudi
python manage.py limpiar_bd --confirm

# Linux/Mac
cd inv_manaudi
python manage.py limpiar_bd --confirm
```
⚠️ **ADVERTENCIA**: Este comando elimina TODOS los datos de usuarios, productos, inventarios, etc.

#### Poblar Base de Datos con Datos Iniciales
```bash
cd inv_manaudi
python manage.py poblar_bd
```

#### Reseteo Completo (Limpiar + Poblar)
```bash
cd inv_manaudi
python manage.py limpiar_bd --confirm
python manage.py poblar_bd
```

### Datos Creados por `poblar_bd`

#### Empresa Principal
- **NINEFIFTEEN**
  - Dirección: Guayaquil
  - Teléfono: 042222222
  - Email: ninefifteen@hotmail.com

#### Sucursales Creadas
1. **Guayaquil** (GYQ) - Punto de Venta
2. **Quito** (UIO) - Punto de Venta  
3. **Cuenca** (CUE) - Punto de Venta
4. **Laboratorio Guayaquil** (LGQ) - Laboratorio
5. **Laboratorio Cuenca** (LCU) - Laboratorio
6. **Laboratorio Quito** (LQU) - Laboratorio

#### Usuarios de Prueba (Contraseña: `1234`)

| Usuario | Nombre | Rol | Sucursal |
|---------|---------|-----|----------|
| `administrador_inventarios` | Edgar Rivas | Administrador | - |
| `ninefifteen_manaudi` | Manaudi Ninefifteen | Manaudi | - |
| `ninefifteen_guayaquil` | Usuario Guayaquil | Supervisor | Guayaquil |
| `ninefifteen_quito` | Usuario Quito | Encargado | Quito |
| `ninefifteen_cuenca` | Usuario Cuenca | Encargado | Cuenca |
| `ninefifteen_administrador` | Stephanny | Supervisor | Guayaquil |
| `ninefifteen_labgye` | Laboratorio Guayaquil | Encargado | Lab Guayaquil |

#### Productos de Ejemplo

| Código | Línea | Sublínea | Clase | Marca | Modelo | Precio |
|--------|--------|----------|-------|--------|---------|---------|
| 900101 | Marco Económico | Hombre | Básica | RAY-BAN | RB3025 | $89.99 |
| 900201 | Marco Económico | Mujer | Básica | VOGUE | VO5239 | $75.50 |
| 900502 | Marco Económico | Unisex | Intermedia | OAKLEY | OX8046 | $120.00 |
| 910103 | Marco Exclusivo | Hombre | Premium | PRADA | PR17WS | $350.00 |
| 910203 | Marco Exclusivo | Mujer | Premium | CHANEL | CH5380 | $450.00 |
| 920503 | Marco Gama Alta | Unisex | Premium | TOM FORD | TF5634 | $580.00 |
| 930501 | Accesorio | Unisex | Básica | GENERIC | CASE-001 | $10.00 |

#### Datos de Inventario
- Inventarios aleatorios (5-50 unidades) en sucursales tipo "punto_venta"
- Stock mínimo aleatorio (3-10 unidades)
- Traslados de ejemplo (pendientes y confirmados)
- Movimientos de inventario de ejemplo

### Flujo de Desarrollo con Datos de Prueba

```bash
# 1. Hacer cambios en modelos
python manage.py makemigrations
python manage.py migrate

# 2. Resetear y poblar con datos de prueba
python manage.py limpiar_bd --confirm
python manage.py poblar_bd

# 3. Crear superusuario si necesitas acceso al admin
python manage.py createsuperuser
```

## Características Especiales

### Sistema de Productos Ópticos
- **Códigos automáticos**: Generación basada en Línea + Sublínea + Clase
- **Clasificación especializada**: 
  - Líneas: ACCESORIO, MARCO ECONOMICO, MARCO EXCLUSIVO, MARCO GAMA ALTA
  - Sublíneas: GAFA, HOMBRE, KID NINA, KID NINO, MUJER, UNISEX
  - Clases: AL AIRE, BASICA, CLIP, INTERMEDIA, PREMIUM
- **Búsqueda avanzada**: Filtros combinables por clasificación
- **Gestión de marca/modelo**: Campos específicos con conversión automática a mayúsculas

### Multi-Tenancy
- Soporte para múltiples empresas en una instancia
- Aislamiento completo de datos entre empresas
- Usuarios pueden pertenecer a una empresa y sucursal

### Workflow de Traslados
1. Usuario origen inicia traslado
2. Sistema crea movimiento de salida automáticamente
3. Traslado queda en estado "pendiente"
4. Usuario destino confirma recepción
5. Sistema crea movimiento de entrada
6. Traslado pasa a estado "confirmado"

### Integración SRI
- Validación de RUC ecuatoriano
- Extracción de información tributaria
- Web scraping del portal SRI

### Dashboard
- Métricas de inventario en tiempo real
- Productos con stock bajo
- Movimientos recientes
- Estadísticas por sucursal

## Notas de Desarrollo

### Pendientes
- Implementación de más reportes
- API REST para integración externa
- Sistema de notificaciones
- Auditoría de cambios

### Consideraciones
- SECRET_KEY expuesta (cambiar en producción)
- DEBUG=True (desactivar en producción)
- Credenciales de BD en código (usar variables de entorno)

### Testing
- No hay tests implementados actualmente
- Estructura preparada en cada app (tests.py)

## Deployment

### PythonAnywhere
- Configuración de BD comentada en settings.py
- ALLOWED_HOSTS incluye dominio PythonAnywhere
- Requiere configuración de STATIC_ROOT

### Requisitos del Servidor
- Python 3.x
- MySQL 5.7+
- Servidor web compatible con WSGI

## Mantenimiento

### Respaldos Recomendados
- Base de datos MySQL diaria
- Carpeta media/ semanal
- Código fuente en control de versiones

### Monitoreo
- Revisar logs de Django
- Monitorear espacio en disco (archivos media)
- Verificar rendimiento de consultas MySQL

## Contacto y Soporte
Sistema desarrollado para Manaudi
Ubicación: Ecuador
Configuración regional: América/Guayaquil