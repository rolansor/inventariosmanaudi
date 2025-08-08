# Setup de Base de Datos - Sistema Inventarios Óptica

## Comandos de Gestión de Base de Datos

Este proyecto incluye comandos personalizados para gestionar la población de la base de datos con datos iniciales.

### 1. Limpiar Base de Datos

Para eliminar todos los datos de la base de datos:

```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

cd inv_manaudi

# Limpiar base de datos (requiere confirmación)
python manage.py limpiar_bd --confirm
```

⚠️ **ADVERTENCIA**: Este comando elimina TODOS los datos de usuarios, productos, inventarios, etc.

### 2. Poblar Base de Datos

Para poblar la base de datos con datos iniciales:

```bash
cd inv_manaudi
python manage.py poblar_bd
```

### 3. Reseteo Completo de Base de Datos

Para un reseteo completo desde cero:

```bash
cd inv_manaudi

# 1. Limpiar datos
python manage.py limpiar_bd --confirm

# 2. Poblar con datos iniciales
python manage.py poblar_bd
```

## Datos Creados por el Script `poblar_bd`

### Empresa
- **NINEFIFTEEN**
  - Dirección: Guayaquil
  - Teléfono: 042222222
  - Email: ninefifteen@hotmail.com

### Sucursales
1. **Guayaquil** (GYQ) - Punto de Venta
2. **Quito** (UIO) - Punto de Venta  
3. **Cuenca** (CUE) - Punto de Venta
4. **Laboratorio Guayaquil** (LGQ) - Laboratorio
5. **Laboratorio Cuenca** (LCU) - Laboratorio
6. **Laboratorio Quito** (LQU) - Laboratorio

### Usuarios (Todos con contraseña: **1234**)

| Usuario | Nombre | Rol | Sucursal |
|---------|---------|-----|----------|
| `administrador_inventarios` | Edgar Rivas | Administrador | - |
| `ninefifteen_manaudi` | Manaudi Ninefifteen | Manaudi | - |
| `ninefifteen_guayaquil` | Usuario Guayaquil | Supervisor | Guayaquil |
| `ninefifteen_quito` | Usuario Quito | Encargado | Quito |
| `ninefifteen_cuenca` | Usuario Cuenca | Encargado | Cuenca |
| `ninefifteen_administrador` | Stephanny | Supervisor | Guayaquil |
| `ninefifteen_labgye` | Laboratorio Guayaquil | Encargado | Lab Guayaquil |

### Grupos de Usuario
- **Administrador**: Acceso total al sistema
- **Manaudi**: Funciones especiales del sistema
- **Supervisor**: Gestión de inventario y reportes
- **Encargado**: Operaciones básicas de inventario

### Productos de Óptica (Ejemplos)

| Código | Línea | Sublínea | Clase | Marca | Modelo | Precio |
|--------|--------|----------|-------|--------|---------|---------|
| 900101 | Marco Económico | Hombre | Básica | RAY-BAN | RB3025 | $89.99 |
| 900201 | Marco Económico | Mujer | Básica | VOGUE | VO5239 | $75.50 |
| 900502 | Marco Económico | Unisex | Intermedia | OAKLEY | OX8046 | $120.00 |
| 910103 | Marco Exclusivo | Hombre | Premium | PRADA | PR17WS | $350.00 |
| 910203 | Marco Exclusivo | Mujer | Premium | CHANEL | CH5380 | $450.00 |
| 920503 | Marco Gama Alta | Unisex | Premium | TOM FORD | TF5634 | $580.00 |
| 930501 | Accesorio | Unisex | Básica | GENERIC | CASE-001 | $10.00 |

### Inventarios Iniciales
- Se crean inventarios aleatorios (5-50 unidades) para todos los productos en las sucursales tipo "punto_venta"
- Stock mínimo aleatorio (3-10 unidades)

### Traslados de Ejemplo
- **Pendiente**: RAY-BAN RB3025 de Guayaquil → Quito (5 unidades)
- **Confirmado**: VOGUE VO5239 de Cuenca → Lab Guayaquil (3 unidades)

### Movimientos de Inventario de Ejemplo
- Entrada: 20 unidades RAY-BAN RB3025 en Guayaquil
- Salida: 2 unidades RAY-BAN RB3025 en Guayaquil (venta)

## Estructura de Códigos de Productos

Los códigos se generan automáticamente concatenando:

**Código = Línea (2 dígitos) + Sublínea (2 dígitos) + Clase (2 dígitos)**

### Líneas
- **90**: MARCO ECONOMICO
- **91**: MARCO EXCLUSIVO
- **92**: MARCO GAMA ALTA
- **93**: ACCESORIO

### Sublíneas
- **01**: HOMBRE
- **02**: MUJER
- **03**: KID NINA
- **04**: KID NINO
- **05**: UNISEX
- **06**: GAFA

### Clases
- **01**: BASICA
- **02**: INTERMEDIA
- **03**: PREMIUM
- **04**: CLIP
- **05**: AL AIRE

## Notas Importantes

1. **Contraseñas**: Todos los usuarios tienen la contraseña `1234` para facilitar el testing
2. **Datos de Ejemplo**: Los productos, inventarios y traslados son datos de ejemplo
3. **Multi-tenant**: El sistema soporta múltiples empresas, pero el script crea solo NINEFIFTEEN
4. **Reseteo Seguro**: Siempre usar los comandos de limpieza antes de repoblar para evitar duplicados

## Uso en Desarrollo

Para desarrollo rápido, puedes usar estos comandos cada vez que hagas cambios grandes en los modelos:

```bash
# 1. Hacer migraciones
python manage.py makemigrations
python manage.py migrate

# 2. Resetear datos
python manage.py limpiar_bd --confirm
python manage.py poblar_bd

# 3. Crear superusuario si necesitas acceso al admin
python manage.py createsuperuser
```

¡Listo para comenzar el desarrollo con datos coherentes!