# Manual de Usuario — Sistema de Inventarios Manaudi

Versión del documento: octubre 2026.

Este manual describe cada pantalla del sistema y cómo usarla. Las pantallas que ve un
usuario dependen de su **rol**; la sección 2 explica los roles y la sección 3 recorre
las pantallas en el orden del menú lateral.

---

## 1. Conceptos básicos

| Concepto | Qué es |
|---|---|
| **Empresa** | Cliente de Manaudi. Cada usuario pertenece a una sola empresa y únicamente ve la información de esa empresa. |
| **Sucursal** | Lugar físico de la empresa donde hay stock: bodega, punto de venta o laboratorio. |
| **Clasificación** | Tres niveles: **Categoría → Subcategoría → Clase**. Cada nivel tiene un código de 3 caracteres y un nombre. Los productos se asignan a una *clase*. |
| **Producto** | Artículo del catálogo: código único, nombre, modelo, precio, tipo (unidad o juego) y clase. Los productos no se borran: se **desactivan**. |
| **Inventario / stock** | Cantidad de un producto en una sucursal. Tiene un **stock mínimo** que dispara alertas. |
| **Movimiento** | Entrada o salida de stock en una sucursal, con su documento de respaldo (factura, nota de venta, etc.). El stock se actualiza automáticamente. |
| **Traslado** | Envío de un producto de una sucursal a otra. Descuenta en origen al iniciarse y suma en destino cuando el receptor **confirma** la cantidad recibida. |

Todo texto de códigos, nombres y descripciones se guarda en **MAYÚSCULAS** automáticamente.

---

## 2. Roles

El acceso se controla por grupos. Un usuario puede tener varios grupos y suma sus permisos.

| Rol | Para quién | Qué puede hacer |
|---|---|---|
| **Manaudi** | Administración de Manaudi | Crear/editar/eliminar empresas y sucursales, eliminar categorías/subcategorías/clases, activar/desactivar productos, carga masiva de productos desde Excel. |
| **Supervisor** | Responsable de la empresa (normalmente en la bodega principal) | Crear y editar la clasificación y los productos, ver la lista completa de productos, consultar movimientos por empresa y por sucursal. |
| **Encargado** | Responsable de una sucursal | Registrar entradas y salidas, iniciar traslados, confirmar la recepción de traslados dirigidos a su sucursal, buscar productos, ver movimientos por producto. |
| **Auditor** | Consulta | Solo lectura: lista de productos y reportes. |
| **Superusuario** | Soporte técnico | Todo lo anterior en cualquier empresa; cambia la empresa activa desde la barra superior y administra usuarios en `/admin/`. |

En la práctica, los usuarios creados por Manaudi tienen: *Manaudi* = los cuatro grupos;
*Supervisor* = Supervisor + Encargado + Auditor; *Encargado* y *Auditor* = solo su grupo.

### Usuario con y sin sucursal

- Un usuario **con sucursal asignada** (supervisores y encargados) registra movimientos
  únicamente en su sucursal y solo puede confirmar traslados **dirigidos a su sucursal**.
  Su dashboard muestra las cifras de esa sucursal.
- Un usuario **sin sucursal** (Manaudi, Auditor, superusuario) ve toda la empresa y puede
  confirmar cualquier traslado de la empresa.

---

## 3. Pantallas

### 3.1 Ingreso al sistema

URL: `/usuarios/login/`

1. Escriba su **usuario** y **contraseña** y pulse **Ingresar**.
2. Si los datos son incorrectos la página se recarga sin mensaje adicional; vuelva a intentarlo.
3. Para salir: menú del usuario (arriba a la derecha) → **Salir Sistema**.

> La casilla "Recuérdame" y el enlace "solicitar un usuario" son decorativos: no tienen
> función. Los usuarios se crean desde el administrador del sistema.

### 3.2 Inicio (dashboard)

URL: `/`

Muestra, para la empresa (y sucursal, si el usuario tiene una):

- **Total de Productos**: productos distintos con inventario.
- **Total Stock Disponible**: suma de unidades.
- **Productos con Bajo Stock**: filas de inventario con cantidad **menor** al stock mínimo.
- **Productos Agotados**: filas de inventario con cantidad 0.
- **Últimos 10 movimientos**: entradas (celeste) y salidas (rosado) con responsable y fecha.

Barra superior: nombre de la **empresa** y **sucursal** del usuario. El superusuario ve
en su lugar un desplegable para **cambiar de empresa**.

### 3.3 Manejo Empresas (rol Manaudi)

Menú: *Manejo Empresas → Lista Empresas* · URL: `/usuarios/empresas/`

- **Crear**: complete Nombre, Dirección, Teléfono y Email y pulse **Crear**. La empresa
  aparece en la tabla sin recargar la página.
- **Editar**: pulse **Editar** en la fila; los datos se cargan en el formulario, modifique
  y pulse **Actualizar**.
- **Eliminar**: pulse **Eliminar** y confirme. ⚠️ Borra también todas sus sucursales,
  usuarios asociados, productos, inventario y movimientos.
- **Sucursales**: abre la pantalla de sucursales de esa empresa.

#### Sucursales

URL: `/usuarios/empresas/<id>/sucursales`

Misma mecánica que empresas. Campos: Nombre, **Abreviatura** (3 letras, ej. UIO),
**Tipo** (Bodega / Punto de Venta / Laboratorio), Dirección y Teléfono.
⚠️ Eliminar una sucursal borra su inventario y sus movimientos.

### 3.4 Categorías (rol Supervisor; eliminar requiere Manaudi)

Menú: *Categorias → Lista Categorias* · URL: `/categorias/lista_categorias/`

1. **Crear Categoría** abre una ventana: código de 3 caracteres (letras/números) y nombre.
2. **Editar** abre la misma ventana con los datos cargados.
3. **Subcategorias** entra al segundo nivel; desde allí el botón **Clases** entra al tercero.
   Las tres pantallas funcionan igual.
4. **Eliminar** (solo Manaudi) borra el nivel y todo lo que contiene. Los productos que
   usaban una clase eliminada quedan "Sin clasificación" y deben reasignarse editándolos.

El código debe ser único dentro de su nivel (dos categorías de la misma empresa no pueden
tener el mismo código; dos subcategorías de la misma categoría tampoco).

### 3.5 Productos

Menú: *Productos*.

#### Nuevo Producto (Supervisor) — `/productos/nuevo/`

| Campo | Obligatorio | Notas |
|---|:-:|---|
| Clasificación | Sí | Buscador con el formato `CAT - Nombre / SUB - Nombre / CLA - Nombre`. |
| Código Principal | Sí | Letras, números y guiones. Único en la empresa. |
| Código Auxiliar | No | Código alternativo (proveedor, anterior, etc.). |
| Código EAN-13 | No | Exactamente 13 dígitos (código de barras). |
| Modelo | No | Autocompleta con los modelos ya usados en la empresa. |
| Nombre | Sí | |
| Descripción | No | |
| Precio | Sí | Hasta 2 decimales; se usa para valorizar el inventario. |
| Tipo | Sí | Unidad o Juego. |

Al guardar vuelve a la lista de productos. Si el código ya existe se muestra un aviso.

#### Lista Productos (Auditor, Supervisor, Manaudi) — `/productos/lista_productos/`

Tabla completa de la empresa con búsqueda, ordenamiento y paginación. Botones para
**copiar, exportar a CSV / Excel / PDF e imprimir**. Los supervisores ven además el botón
de **editar** en cada fila.

#### Búsqueda Productos (Encargado y superiores) — `/productos/busqueda/`

Escriba parte del código, código auxiliar, EAN, modelo, nombre o descripción y/o elija
una categoría; pulse **Buscar**. Sin filtros no se muestran resultados.
En cada resultado, según el rol:

- ✏️ **Editar** (Supervisor).
- 🚫 **Desactivar** / ✔️ **Activar** (Manaudi). Pide confirmación. Un producto inactivo
  se muestra en gris; sigue apareciendo en listas y selectores (con su estado), pero
  indica que ya no se comercializa.

#### Editar Producto (Supervisor) — `/productos/editar/<id>/`

Mismos campos que el alta. Tras guardar permanece en la pantalla con el mensaje
"Producto actualizado con éxito".

### 3.6 Mantenimiento Inventario (rol Encargado y superiores)

#### Entrada/Salida — `/inventario/movimiento_inventario/`

1. **Sucursal**: fija si el usuario tiene sucursal; si no, elija una.
2. **Producto**: buscador por código y nombre.
3. **Tipo Movimiento**: Entrada o Salida.
4. **Cantidad**: entero mayor a 0.
5. **Comentario**: texto libre con sugerencias (COMPRA PRODUCTOS, DEVOLUCIÓN, AJUSTE…).
   Al elegir *INVENTARIO INICIAL* el documento de respaldo se completa con `000-000-000000000`.
6. **Tipo de Documento**: Nota de Venta, Factura, Orden de Trabajo, Nota de Pedido u Otros.
7. **Documento Respaldo**: número del documento (obligatorio).
8. **Documento Soporte**: archivo adjunto opcional (máximo 5 MB).
9. **Registrar Movimiento**. El stock se actualiza al instante.

Una **salida mayor al stock disponible** se rechaza con el mensaje
*"Stock insuficiente para la salida solicitada"* y no modifica nada.
Debajo del formulario se listan los 20 movimientos más recientes de la empresa.

> Los movimientos no se editan ni se borran. Un error se corrige con un movimiento
> contrario (por ejemplo una entrada con comentario *CORRECCIÓN DE STOCK*).

#### Traslados — `/inventario/traslado/iniciar/`

1. Elija **Sucursal Origen**, **Sucursal Destino** (distintas), **Producto** y
   **Cantidad Entregada**.
2. Indique **Tipo de Documento** (Guía de Remisión, Guía Servientrega, Orden de Trabajo,
   Otros), el **Documento Respaldo** y opcionalmente un archivo.
3. **Registrar Traslado**.

En ese momento se descuenta el stock en origen (movimiento de salida automático) y el
traslado queda **Pendiente**: la mercadería está "en tránsito". Si el origen no tiene
stock suficiente, el traslado se rechaza. La tabla inferior muestra los 10 últimos traslados.

#### Acuse Recibo — `/inventario/traslados_pendientes/`

Lista los traslados pendientes. Un encargado ve solo los dirigidos a su sucursal; un
supervisor o un usuario sin sucursal ve todos los de la empresa.

1. Pulse **Confirmar Recepción** en el traslado recibido.
2. Escriba la **Cantidad Recibida** (mayor a 0). Puede ser **distinta** de la entregada
   si llegó con faltantes o sobrantes: la diferencia queda registrada.
3. **Confirmar Recepción**. Se genera la entrada en la sucursal destino y el traslado pasa
   a **Confirmado**.

Si un traslado muestra *No Disponible* es porque no está dirigido a su sucursal.

#### Movimientos

- **Producto** (`/inventario/producto_movimientos/`): elija un producto y pulse **Buscar
  Movimientos**. Muestra un resumen (entradas y salidas normales, stock actual total,
  traslados enviados/recibidos, unidades en tránsito, diferencia enviado vs. recibido) y
  tres pestañas con el detalle: Entradas, Salidas y Traslados.
- **Empresa** (Supervisor, `/inventario/empresa_movimientos/`): historial completo de
  movimientos y de traslados de la empresa.
- **Sucursal** (Supervisor, `/inventario/sucursal_movimientos/`): elija una sucursal;
  muestra sus movimientos y los traslados en que participa como origen o destino.

### 3.7 Reportes (rol Auditor y superiores)

Ambos reportes tienen un botón de **imprimir** (usa la impresión del navegador; desde
allí puede guardarse como PDF).

#### Movimientos del Día — `/reportes/reporte_diario/`

Movimientos registrados **hoy** en la empresa: tarjetas con usuarios activos, totales por
tipo y total de movimientos; pestañas con el detalle hora a hora, el resumen por usuario y
el resumen por tipo. Incluye las salidas y entradas generadas por traslados.

#### Inventario Valorizado — `/reportes/inventario_valorizado/`

Valor del stock (cantidad × precio) de la empresa. Tarjetas con productos, unidades, valor
total y cantidad de alertas. Pestañas:

- **Detalle**: cada producto en cada sucursal con su valor.
- **Por Sucursal** y **Por Categoría**: totales agrupados.
- **Top 10**: productos de mayor valor en inventario.
- **Alertas**: productos con cantidad menor o igual al stock mínimo.

#### Carga Masiva de Productos (Manaudi) — `/reportes/carga_masiva/`

Permite crear o actualizar muchos productos desde un Excel.

1. **Descargar Plantilla Excel**: trae filas de ejemplo con la clasificación real de la
   empresa y hojas de referencia (Instrucciones, Categorías, Subcategorías, Clases, Sucursales).
2. Complete las columnas. Obligatorias: `codigo`, `nombre`, `categoria`, `subcategoria`,
   `clase`. Opcionales: `modelo`, `precio`, `tipo_producto` (unidad/juego), `descripcion`,
   `stock_minimo`, `sucursal`, `cantidad_inicial`.
3. Borre las filas de ejemplo, guarde como **.xlsx** y arrástrelo a la pantalla (o
   **Seleccionar archivo**) y pulse **Procesar Archivo**.

Comportamiento:

- La clasificación se busca **por nombre**; si no existe se crea con un código automático
  de 3 caracteres.
- Si el `codigo` ya existe en la empresa, el producto se **actualiza**; si no, se crea.
- Si vienen `sucursal` (por nombre) y `cantidad_inicial`, se fija ese stock en la sucursal
  (reemplaza el saldo anterior; no genera movimiento).
- Al terminar se informa cuántos se crearon/actualizaron y los errores por fila (máximo 10 en pantalla).

### 3.8 Administrador del sistema (superusuario)

URL: `/admin/`. Aquí se gestionan los **usuarios**:

1. *Usuarios → Añadir*: nombre de usuario, contraseña, nombre, apellido, correo y, en
   **Grupos**, el o los roles.
2. *Perfiles de usuario → Añadir*: elija el usuario, su **empresa** y (opcional) su
   **sucursal**. Sin perfil el usuario no verá datos.

También puede consultar y corregir desde el admin empresas, sucursales, clasificación,
productos e inventario. ⚠️ No modifique movimientos ni traslados desde aquí.

---

## 4. Preguntas frecuentes

**No veo una opción del menú.** Su usuario no tiene el grupo necesario. Pida al
administrador que lo agregue al grupo correspondiente (sección 2).

**Aparece "Acceso Denegado".** Intentó abrir una pantalla para la que no tiene permiso.

**No puedo confirmar un traslado ("No Disponible").** El traslado va a otra sucursal.
Solo el encargado de la sucursal destino, o un usuario sin sucursal, puede confirmarlo.

**Me equivoqué en un movimiento.** Registre el movimiento contrario con el comentario
CORRECCIÓN DE STOCK y el mismo documento de respaldo.

**El producto no aparece en el buscador del movimiento.** Verifique que esté creado en
su empresa (Productos → Lista Productos). Los productos inactivos sí aparecen.

**Quiero borrar un producto.** No es posible; desactívelo (Manaudi) desde Búsqueda Productos.
