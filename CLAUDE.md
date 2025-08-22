# Sistema de Inventarios Manaudi - Documentación para Claude

## 🏗️ Arquitectura del Proyecto

### Stack Tecnológico
- **Framework**: Django 3.2.25
- **Base de Datos**: MySQL (PyMySQL)
- **Frontend**: Templates Django con Bootstrap 5
- **Autenticación**: Sistema customizado con modelo Usuario personalizado

## 📁 Estructura del Proyecto

```
inv_manaudi/
├── usuarios/        # Gestión de usuarios, empresas y sucursales
├── inventario/      # Control de inventarios y movimientos
├── productos/       # Administración de productos
├── categorias/      # Categorías y subcategorías
├── auxiliares/      # Funciones auxiliares
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

### Roles y Permisos Detallados

#### 1. **Administrador** (Control total del sistema)
**Permisos:**
- Gestión completa de empresas (crear, listar)
- Gestión completa de sucursales (crear, listar)
- Gestión completa de usuarios (crear, editar, listar)
- Eliminar categorías y subcategorías
- Eliminar y desactivar productos
- Acceso a todas las funciones de otros roles

#### 2. **Supervisor** (Gestión operativa y reportes)
**Permisos:**
- Crear y listar categorías
- Crear y listar subcategorías
- Gestión completa de productos (crear, editar, listar, buscar)
- Iniciar traslados entre sucursales
- Ver traslados pendientes
- Generar reportes diarios
- Ver movimientos por empresa
- Acceso a inventarios

#### 3. **Encargado** (Operaciones diarias de inventario)
**Permisos:**
- Registrar movimientos de inventario (entradas/salidas)
- Confirmar traslados recibidos
- Ver movimientos por producto
- Ver movimientos por sucursal
- Operaciones básicas de inventario

#### 4. **Manaudi** (Rol especial con acceso limitado)
**Permisos:**
- Consulta de IDs en módulo auxiliares
- Posiblemente rol de auditoría o consulta

**Jerarquía de permisos**: Administrador > Supervisor > Encargado > Manaudi

## 🌐 URLs y Endpoints Principales

### /usuarios/
- login/, logout/, registro/
- empresas/, sucursales/
- editar/

### /inventario/
- movimiento_inventario/
- traslado/iniciar/
- traslados_pendientes/
- producto_movimientos/, empresa_movimientos/, sucursal_movimientos/

### /productos/
- nuevo/, lista_productos/
- busqueda/, editar/<id>/, eliminar/<id>/
- bsq_por_codigo/

### /categorias/
- nueva_categoria/, lista_categorias/
- <id>/nueva_subcategoria/, <id>/lista_subcategorias/

### /reportes/
- reporte_diario/

### /auxiliares/
- consulta_id/

## ⚙️ Configuración Importante (settings.py)

### Base de Datos
- **Local**: MySQL en localhost, DB: inv_manaudi
- **Producción** (comentado): PythonAnywhere
- **Credenciales**: root/f4d3s2a1 (⚠️ CAMBIAR EN PRODUCCIÓN)

### Seguridad
- **SECRET_KEY**: Expuesta (⚠️ CAMBIAR EN PRODUCCIÓN)
- **DEBUG**: True (⚠️ Desactivar en producción)
- **ALLOWED_HOSTS**: ['sifcol.pythonanywhere.com', 'localhost']

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
- SECRET_KEY expuesta en settings.py
- DEBUG=True en producción
- Credenciales de BD hardcodeadas

### Migraciones Pendientes
- Carpetas de migraciones creadas pero posiblemente sin aplicar:
  - inventario/migrations/
  - productos/migrations/
  - usuarios/migrations/

### Validaciones Críticas
- Stock insuficiente en salidas
- Sucursales de misma empresa en traslados
- Cantidad recibida en confirmación de traslados

## 📝 Notas de Desarrollo

### Helpers Importantes
- `obtener_empresa(request)`: Obtiene empresa del usuario logueado
- `control_acceso`: Decorador para verificar permisos
- Managers personalizados en Producto para filtrar por empresa

### Plantillas Base
- base.html: Template principal con Bootstrap 5
- DataTables integrado para listados
- Select2 para selectores mejorados

### Assets
- Bootstrap 5 + FontAwesome
- jQuery + DataTables
- Plugins: Select2, Bootstrap Datepicker, PDFMake

## 🔧 Comandos Útiles

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Servidor de desarrollo
python manage.py runserver

# Crear superusuario
python manage.py createsuperuser

# Poblar base de datos con datos de prueba
python manage.py populate_data                  # Crea datos de prueba
python manage.py populate_data --clear          # Limpia y recrea todos los datos
python manage.py populate_data --empresas 2     # Crea solo 2 empresas
```



## 👥 Usuarios del Sistema

### Comando populate_data
El comando `python manage.py populate_data` crea automáticamente usuarios de prueba con la siguiente estructura:

**NOTA**: Todas las contraseñas son: **1234**

### Usuarios Creados por Empresa

#### TechCorp Ecuador
| Usuario | Nombre | Rol | Sucursal | Email |
|---------|--------|-----|----------|-------|
| **admin** | Super Admin | Superusuario | - | admin@sistema.com |
| **techcorp_admin** | Admin TechCorp | Administrador | - | admin@techcorp.com |
| **techcorp_supervisor** | Supervisor TechCorp | Supervisor | Matriz Quito | supervisor@techcorp.com |
| **techcorp_encargado** | Encargado TechCorp | Encargado | Sucursal Guayaquil | encargado@techcorp.com |
| **techcorp_manaudi** | Manaudi TechCorp | Manaudi | - | manaudi@techcorp.com |

#### Comercial Andina
| Usuario | Nombre | Rol | Sucursal | Email |
|---------|--------|-----|----------|-------|
| **comercia_admin** | Admin Comercial | Administrador | - | admin@comercia.com |
| **comercia_supervisor** | Supervisor Comercial | Supervisor | Bodega Principal | supervisor@comercia.com |
| **comercia_encargado** | Encargado Comercial | Encargado | Punto Venta Norte | encargado@comercia.com |
| **comercia_manaudi** | Manaudi Comercial | Manaudi | - | manaudi@comercia.com |

#### Distribuidora Nacional
| Usuario | Nombre | Rol | Sucursal | Email |
|---------|--------|-----|----------|-------|
| **distribu_admin** | Admin Distribuidora | Administrador | - | admin@distribu.com |
| **distribu_supervisor** | Supervisor Distribuidora | Supervisor | Centro Distribución | supervisor@distribu.com |
| **distribu_encargado** | Encargado Distribuidora | Encargado | Tienda Cuenca | encargado@distribu.com |
| **distribu_manaudi** | Manaudi Distribuidora | Manaudi | - | manaudi@distribu.com |

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
    │   ADMIN   │                   │   ADMIN   │                   │   ADMIN   │
    │ techcorp_ │                   │ comercia_ │                   │ distribu_ │
    │   admin   │                   │   admin   │                   │   admin   │
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
  │   MANAUDI     │               │   MANAUDI     │               │   MANAUDI     │
  │ techcorp_     │               │ comercia_     │               │ distribu_     │
  │  manaudi      │               │  manaudi      │               │  manaudi      │
  │ (Auditoría)   │               │ (Auditoría)   │               │ (Auditoría)   │
  └───────────────┘               └───────────────┘               └───────────────┘

SUCURSALES POR EMPRESA:
──────────────────────

TechCorp Ecuador:           Comercial Andina:           Distribuidora Nacional:
• Matriz Quito (UIO)        • Bodega Principal (BOD)    • Centro Distribución (CDI)
• Sucursal Guayaquil (GYE)  • Punto Venta Norte (PVN)   • Tienda Cuenca (CUE)
• Laboratorio Quito (LAB)   • Punto Venta Sur (PVS)     • Tienda Loja (LOJ)
```

### Matriz de Permisos por Rol

| Funcionalidad | Administrador | Supervisor | Encargado | Manaudi |
|--------------|:-------------:|:----------:|:---------:|:-------:|
| **Gestión de Empresas** | ✅ | ❌ | ❌ | ❌ |
| **Gestión de Sucursales** | ✅ | ❌ | ❌ | ❌ |
| **Gestión de Usuarios** | ✅ | ❌ | ❌ | ❌ |
| **Categorías - Crear/Listar** | ✅ | ✅ | ❌ | ❌ |
| **Categorías - Eliminar** | ✅ | ❌ | ❌ | ❌ |
| **Productos - Crear/Editar** | ✅ | ✅ | ❌ | ❌ |
| **Productos - Eliminar** | ✅ | ❌ | ❌ | ❌ |
| **Iniciar Traslados** | ✅ | ✅ | ❌ | ❌ |
| **Confirmar Traslados** | ✅ | ✅ | ✅ | ❌ |
| **Movimientos Inventario** | ✅ | ✅ | ✅ | ❌ |
| **Reportes** | ✅ | ✅ | ❌ | ❌ |
| **Consulta IDs (Auxiliares)** | ✅ | ✅ | ✅ | ✅ |

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

1. **Seguridad**: Cambiar SECRET_KEY y desactivar DEBUG en producción
2. **Variables de Entorno**: Mover credenciales a archivo .env
3. **Tests**: Agregar pruebas unitarias y de integración
4. **API REST**: Considerar agregar Django REST Framework
5. **Documentación**: Agregar docstrings en vistas y modelos
6. **Logs**: Implementar sistema de logging
7. **Backups**: Configurar respaldos automáticos de BD