# Guion de demostración — Sistema de Inventarios Manaudi

Recorrido sugerido para el video ilustrativo y la capacitación. Usa los datos que crean
`populate_data` + `populate_demo` (empresa **TechCorp Ecuador**). Duración estimada:
20–25 minutos. Todas las contraseñas son `1234`.

Antes de grabar:

```bash
docker compose up -d
# si la base está vacía o se quiere reiniciar la demo:
docker compose exec web python manage.py populate_data --clear
docker compose exec web python manage.py populate_demo
```

Abrir <http://127.0.0.1:8012> en Chrome (ventana de 1366×768 o mayor, zoom 100 %).

> Los números exactos (stock, cantidades) pueden variar si se regeneran los datos; los
> nombres de productos, sucursales y usuarios no cambian.

---

## Escena 1 — Administración (usuario `techcorp_manaudi`)

**Qué mostrar:** la estructura de la empresa.

1. Login como `techcorp_manaudi`. Señalar la cabecera: *EMPRESA: TechCorp Ecuador*, sin sucursal.
2. Dashboard: tarjetas (productos, stock, bajo stock, agotados) y últimos movimientos.
   Mencionar que hay **1 producto agotado** (Silla Ejecutiva en Laboratorio Quito) y varios
   con bajo stock.
3. Menú *Manejo Empresas → Lista Empresas*: tres empresas. Explicar que cada una está aislada.
4. **Sucursales** de TechCorp: Matriz Quito (Bodega, UIO), Sucursal Guayaquil (Punto de
   Venta, GYE), Laboratorio Quito (Laboratorio, LAB).
   - Crear una sucursal de prueba "Bodega Norte", abreviatura `BNO`, tipo Bodega → aparece
     sin recargar. Editarla (cambiar dirección) y eliminarla.
5. Menú *Categorias → Lista Categorias*: ELE – Electrónica y OFI – Oficina.
   - Entrar a **Subcategorias** de Electrónica (COM, CEL) y a **Clases** de Computadoras
     (LAP, DES, TAB). Explicar el código de 3 caracteres y la jerarquía.
   - Crear una clase `MON – MONITORES` en Computadoras; luego eliminarla (botón rojo, solo Manaudi).
6. *Reportes → Carga Masiva de Productos*: descargar la plantilla, abrirla en Excel y
   mostrar las hojas de referencia. (Opcional: cargar una fila nueva `TEC_MON001 –
   MONITOR 24"` y mostrar el mensaje de resultado.)
7. *Productos → Busqueda Productos*: buscar `ESC` → aparece **ESCRITORIO 1.5M** en gris
   (inactivo). Pulsar ✔️ **Activar** y luego 🚫 **Desactivar** para mostrar el ciclo.
8. Cerrar sesión.

## Escena 2 — Supervisor de la bodega (usuario `techcorp_supervisor`)

**Qué mostrar:** catálogo y despacho desde la bodega principal.

1. Login como `techcorp_supervisor`. Cabecera: *SUCURSAL: Matriz Quito*. El dashboard
   muestra solo cifras de la Matriz.
2. *Productos → Nuevo Producto*: crear
   - Clasificación: `ELE - ELECTRÓNICA / COM - COMPUTADORAS / TAB - TABLETS`
   - Código `TEC_TAB002`, código EAN `7861234567890`, modelo `GALAXY-TAB-S9` (mostrar el
     autocompletado de modelos), nombre `Tablet Samsung Galaxy Tab S9`, precio `450`.
   - Guardar → redirige a la lista. Mostrar que quedó en MAYÚSCULAS.
3. *Lista Productos*: buscar "LAPTOP", ordenar por precio, exportar a Excel o PDF.
4. *Mantenimiento Inventario → Entrada/Salida*: registrar una **entrada** del nuevo
   producto `TEC_TAB002`, cantidad 20, comentario `COMPRA PRODUCTOS`, tipo Factura,
   documento `001-001-000012345`, adjuntar un PDF cualquiera (opcional). La sucursal está
   fija en Matriz Quito. Verificar el movimiento en la tabla inferior.
5. Intentar una **salida** de 999 unidades de `TEC_HOJ001 – RESMA PAPEL A4` → mensaje
   *Stock insuficiente*. Explicar la validación.
6. *Mantenimiento Inventario → Traslados*: origen Matriz Quito, destino Sucursal
   Guayaquil, producto `TEC_TAB002`, cantidad 5, Guía de Remisión `GR-0001`. Registrar →
   redirige a **Acuse Recibo**: el traslado aparece como pendiente; como el supervisor está
   en la Matriz, el botón dice *No Disponible* para los destinados a GYE.
7. *Movimientos → Producto*: elegir `TEC_LAP002 – LAPTOP HP PROBOOK`. Mostrar el resumen:
   entradas/salidas normales, stock total, traslados enviados vs. recibidos y la
   **diferencia** (el traslado a Laboratorio llegó con 1 unidad faltante: 7 entregadas,
   6 recibidas). Recorrer las pestañas Entradas / Salidas / Traslados.
8. *Movimientos → Empresa* y *Movimientos → Sucursal* (elegir Laboratorio Quito):
   historial completo con buscador.
9. Cerrar sesión.

## Escena 3 — Encargado de la sucursal (usuario `techcorp_encargado`)

**Qué mostrar:** operación diaria en un punto de venta y recepción de traslados.

1. Login como `techcorp_encargado`. Cabecera: *SUCURSAL: Sucursal Guayaquil*. Dashboard
   con cifras solo de Guayaquil; señalar los productos con bajo stock de la sucursal
   (p. ej. `RESMA PAPEL A4` con 2 unidades).
2. Menú reducido: solo Productos (búsqueda) y Mantenimiento Inventario. Intentar entrar a
   `/productos/lista_productos/` por URL → pantalla **Acceso Denegado**.
3. *Acuse Recibo*: aparecen los traslados pendientes hacia Guayaquil (iPhone 13 ×7,
   Samsung Galaxy S21 ×3 y la Tablet de la escena anterior ×5).
   - Confirmar la **Tablet**: cantidad recibida 5 → *Recepción confirmada*.
   - Confirmar el **iPhone 13** con cantidad recibida **6** (llegó uno menos): explicar que
     la diferencia queda registrada.
4. *Entrada/Salida*: registrar una **salida** de 1 `TEC_TAB002`, Nota de Venta
   `001-002-000000456`, comentario `VENTA AL CLIENTE`. La sucursal viene fija.
5. *Busqueda Productos*: buscar `IPHONE`; mostrar que el encargado no tiene botones de
   editar/activar.
6. *Movimientos → Producto*: `TEC_TAB002` → se ven la entrada en Matriz, el traslado
   confirmado y la salida en Guayaquil; stock total 19.
7. Cerrar sesión.

## Escena 4 — Auditoría (usuario `techcorp_auditor`)

**Qué mostrar:** solo lectura y reportes.

1. Login como `techcorp_auditor`. Menú: Productos (lista) y Reportes.
2. *Reportes → Movimientos del Día*: hoy hay movimientos de las tres escenas anteriores
   más los generados por la demo; recorrer Detalle / Por Usuario / Por Tipo. Botón imprimir.
3. *Reportes → Inventario Valorizado*: tarjetas de totales; pestañas Por Sucursal, Por
   Categoría, Top 10 (los celulares y laptops encabezan) y **Alertas** (stock bajo y la
   Silla Ejecutiva agotada en Laboratorio).
4. *Lista Productos*: sin botón de editar.
5. Cerrar sesión.

## Escena 5 — Superusuario y administración de usuarios (usuario `admin`)

**Qué mostrar:** soporte multi-empresa y alta de usuarios.

1. Login como `admin`. En la cabecera, desplegable **EMPRESA**: cambiar a *Comercial
   Andina* → el dashboard y todos los listados pasan a esa empresa. Volver a TechCorp.
2. Ir a `/admin/`:
   - *Usuarios → Añadir*: `techcorp_vendedor`, contraseña, nombre; en Grupos agregar
     **Encargado**. Guardar.
   - *Perfiles de usuario → Añadir*: usuario `techcorp_vendedor`, empresa TechCorp,
     sucursal Laboratorio Quito.
   - *Grupos → Encargado*: mostrar el selector de usuarios del grupo.
3. (Opcional) Login como `techcorp_vendedor` para mostrar que ve solo Laboratorio Quito.

## Cierre

- Resumen de roles (tabla del README).
- Dónde está la documentación: `README.md`, `docs/manual_usuario.md`, `docs/manual_tecnico.md`.
- Cómo levantar el entorno: `docker compose up -d`.
