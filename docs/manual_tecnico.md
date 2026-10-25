# Manual Técnico — Sistema de Inventarios Manaudi

Versión del documento: octubre 2026 · Django 4.2.30 · Python 3.10 · MySQL 8.

Este documento está dirigido a quien deba mantener, desplegar o extender el sistema.
Complementa a los docstrings del código y al [README](../README.md).

---

## 1. Arquitectura

Aplicación Django monolítica con plantillas renderizadas en el servidor. No hay API REST
ni frontend separado; las interacciones dinámicas (alta/edición en listados, tabla de
productos) usan jQuery + AJAX contra las mismas vistas, que responden JSON cuando la
petición es `XMLHttpRequest` (helper `usuarios.utils.es_ajax`).

```
Navegador ──HTTP──▶ Django (runserver en Docker / WSGI en PythonAnywhere)
                      │  usuarios · categorias · productos · inventario · reportes
                      ▼
                    MySQL 8 (PyMySQL, charset utf8mb4)
```

### Apps

| App | Responsabilidad | Modelos |
|---|---|---|
| `usuarios` | Empresas, sucursales, usuario personalizado y perfil; login/logout; dashboard; helper `obtener_empresa`; decorador `control_acceso`; context processor de empresa | `Empresa`, `Sucursal`, `Usuario`, `UsuarioPerfil` |
| `categorias` | Clasificación en tres niveles | `Categoria`, `Subcategoria`, `Clase` |
| `productos` | Catálogo | `Producto` |
| `inventario` | Stock por sucursal, movimientos y traslados (toda la lógica de stock) | `Inventario`, `MovimientoInventario`, `Traslado` |
| `reportes` | Reporte diario, inventario valorizado, carga masiva Excel y plantilla | — |

### Dependencias de importación entre apps

```
usuarios ◀── categorias ◀── productos ◀── inventario ◀── reportes
   ▲                                          │
   └──────────────────────────────────────────┘  (usuarios.views importa inventario.models para el dashboard)
```

`usuarios.context_processors` importa `usuarios.views`; evitar importar
`context_processors` desde las vistas para no crear ciclos.

### Layout y estáticos

- `inv_manaudi/templates/base.html`: cabecera (empresa/sucursal o selector para
  superusuario), menú lateral condicionado por grupo con el filtro `pertenece_grupo`,
  bloques `title`, `extra_css`, `encabezado`, `contenido`, `extra_js`.
- `inv_manaudi/static/`: tema **Color Admin** (Bootstrap 5), FontAwesome, jQuery,
  DataTables (+ Buttons, Responsive, PDFMake, JSZip), Select2, Bootstrap Datepicker.
  Algunas plantillas de productos cargan Select2 y jQuery Mask desde CDN.
- No copiar los estáticos del admin de Django dentro de `static/`: pisarían los de la
  versión instalada.

---

## 2. Modelo de datos

```
Empresa 1──n Sucursal
Empresa 1──n UsuarioPerfil n──1 Usuario(AbstractUser)      (UsuarioPerfil.sucursal opcional)
Empresa 1──n Categoria 1──n Subcategoria 1──n Clase 1──n Producto n──1 Empresa
Producto 1──n Inventario n──1 Sucursal                      (único por producto+sucursal)
Producto 1──n MovimientoInventario n──1 Sucursal
Producto 1──n Traslado  (sucursal_origen, sucursal_destino, movimiento_salida, movimiento_entrada)
```

### usuarios

| Modelo | Campos relevantes | Reglas |
|---|---|---|
| `Empresa` | nombre, direccion, telefono, email, fecha_creacion | Raíz del aislamiento multi-empresa. |
| `Sucursal` | empresa (FK CASCADE), nombre, abreviatura (3), direccion, telefono, tipo_sucursal {bodega, punto_venta, laboratorio} | |
| `Usuario` | AbstractUser + telefono, direccion | `AUTH_USER_MODEL = 'usuarios.Usuario'`. |
| `UsuarioPerfil` | usuario (O2O, `related_name='perfil'`), empresa, sucursal (nullable) | `clean()` exige que la sucursal pertenezca a la empresa. Los superusuarios pueden no tener perfil. |

### categorias

Los tres modelos tienen `codigo` (3 alfanuméricos, `RegexValidator`), `nombre`, y
`save()` que pasa ambos a mayúsculas. Unicidad: `Categoria(codigo, empresa)`,
`Subcategoria(codigo, categoria)`, `Clase(codigo, subcategoria)`. Borrado en cascada
hacia abajo; `Producto.clase` es `SET_NULL`.

### productos

| Campo | Tipo | Notas |
|---|---|---|
| codigo | CharField(50) | Único por empresa (`UniqueConstraint unique_codigo_empresa`). Mayúsculas. |
| codigo_auxiliar | CharField(50), opcional | Mayúsculas. |
| codigo_ean | CharField(13), opcional | El formulario exige 13 dígitos; el modelo no valida. |
| modelo | CharField(100), opcional | Mayúsculas. Autocompletado vía `obtener_modelos_unicos`. |
| nombre, descripcion | | Mayúsculas. |
| precio | Decimal(10,2) | Usado por el inventario valorizado. |
| tipo_producto | {unidad, juego} | Informativo. |
| clase | FK Clase, SET_NULL | |
| estado | {activo, inactivo} | Los productos no se borran. |
| empresa | FK Empresa, CASCADE | |

Manager: `Producto.objects.para_empresa(empresa)`.

### inventario

| Modelo | Campos | Reglas |
|---|---|---|
| `Inventario` | sucursal, producto, cantidad, stock_minimo, ultima_actualizacion (auto_now) | Único por (sucursal, producto). `is_stock_bajo()`, `valor_inventario()`. |
| `MovimientoInventario` | sucursal, producto, tipo_movimiento {entrada, salida}, tipo_documento {nota_venta, factura, orden_trabajo, nota_pedido, otros}, cantidad, fecha (auto_now_add), comentario, documento_respaldo, documento_soporte (FileField → `media/documento_soporte/`), usuario (SET_NULL) | Ver §3.1. |
| `Traslado` | producto, sucursal_origen, sucursal_destino, cantidad_entregada, cantidad_recibida, estado {pendiente, confirmado}, fecha_creacion, usuario, tipo_documento {guia_remision, guia_servientrega, orden_trabajo, otros}, documento_respaldo, documento_soporte, movimiento_salida, movimiento_entrada (FK a MovimientoInventario, SET_NULL, related_name `traslado_salida` / `traslado_entrada`) | Ver §3.2. |

### Migraciones

Las migraciones del repo se regeneraron el 18/10/2026 con los mismos nombres que las
aplicadas en producción (`0001_initial`, `0002_initial`, `0003_initial`,
`0002_traslado_producto`). `makemigrations --check` no debe detectar cambios. El
contenedor `web` corre `migrate` al iniciar (`RUN_MIGRATIONS=1`).

---

## 3. Reglas de negocio e integridad

### 3.1 Movimientos (`MovimientoInventario.save`)

- Solo al **crear** (`pk is None`): dentro de `transaction.atomic()`, hace
  `Inventario.objects.select_for_update().get_or_create(sucursal, producto)`, suma o
  resta y guarda ambos. El bloqueo de fila evita condiciones de carrera.
- Salida con `cantidad > inventario.cantidad` → `ValueError('Stock insuficiente...')`;
  las vistas lo capturan y lo muestran como error del formulario.
- Al **editar** un movimiento existente no se toca el stock. Por eso `MovimientoInventario`
  y `Traslado` **no están registrados en el admin** y la UI no permite editar ni borrar
  movimientos. Las correcciones se hacen con movimientos contrarios.
- La carga masiva (`cantidad_inicial`) y `populate_data` fijan `Inventario.cantidad`
  directamente, sin movimiento; el kardex de "Movimientos por producto" no refleja ese
  saldo inicial.

### 3.2 Traslados (`Traslado.save` / `Traslado.confirmar`)

1. `save()` nuevo: valida origen ≠ destino, crea el movimiento de **salida** en origen
   (misma transacción) y guarda con `estado='pendiente'`.
2. `confirmar()`: exige `estado == 'pendiente'` y `cantidad_recibida > 0`; crea el
   movimiento de **entrada** en destino por `cantidad_recibida`, enlaza
   `movimiento_entrada` y pasa a `confirmado`.
3. Decisión de negocio: **no** se valida que `cantidad_recibida == cantidad_entregada`.
   La diferencia se expone en "Movimientos por producto" (`diferencia_traslados`).
4. Ambas sucursales deben ser de la misma empresa; el formulario (`TrasladoForm(empresa=...)`)
   acota los selectores. No se restringe que el origen sea la sucursal del usuario.

### 3.3 Aislamiento multi-empresa

- `usuarios.views.obtener_empresa(request)`: superusuario → `session['empresa_id']`
  (o la primera empresa); usuario normal → `perfil.empresa`.
- Toda vista de negocio filtra por esa empresa, y los `get_object_or_404` incluyen la
  empresa en el filtro (un ID de otra empresa devuelve 404).
- El context processor `empresa_context` expone `empresa_actual` y, para superusuarios,
  `todas_las_empresas` (selector de la cabecera → `cambiar_empresa`).

### 3.4 Permisos

- `usuarios.templatetags.tags.control_acceso('<Grupo>')`: anónimo → login con `?next=`;
  sin grupo → `acceso_denegado.html` HTTP 403.
- Un decorador = un grupo. No hay herencia: Manaudi tiene los cuatro grupos, Supervisor
  tiene Supervisor + Encargado + Auditor (así los crea `populate_data`).
- Usuario **con sucursal**: `MovimientoInventarioForm` fija la sucursal;
  `confirmar_traslado` solo permite traslados destinados a su sucursal
  (`inventario.views._puede_confirmar`). `traslados_pendientes` muestra todos a los
  Supervisores y a quienes no tienen sucursal; al resto solo los de su sucursal.

| Vista | Grupo |
|---|---|
| empresa_list, empresa_edit, empresa_delete, sucursal_list, sucursal_edit, sucursal_delete | Manaudi |
| nueva/lista/editar categoría, subcategoría, clase | Supervisor |
| eliminar categoría, subcategoría, clase | Manaudi |
| crear_producto, editar_producto, obtener_modelos_unicos | Supervisor |
| lista_productos, bsq_por_codigo | Auditor |
| busqueda_producto | Encargado |
| desactivar_producto, activar_producto | Manaudi |
| movimiento_inventario, iniciar_traslado, traslados_pendientes, confirmar_traslado, movimientos_por_producto | Encargado |
| movimientos_por_empresa, movimientos_por_sucursal | Supervisor |
| reporte_movimientos_dia, reporte_inventario_valorizado | Auditor |
| carga_masiva_productos, descargar_plantilla_productos | Manaudi |
| inicio, cambiar_empresa | login_required |

---

## 4. Rutas

| URL | Vista | Método | Respuesta |
|---|---|---|---|
| `/` | usuarios.inicio | GET | HTML |
| `/admin/` | Django admin | | |
| `/usuarios/login/`, `/usuarios/logout/` | login_view, logout_view | GET/POST | HTML / redirect |
| `/usuarios/empresas/` | empresa_list | GET, POST | HTML; POST AJAX → JSON |
| `/usuarios/empresas/editar/<pk>/` | empresa_edit | GET AJAX, POST | JSON |
| `/usuarios/empresas/eliminar/<pk>/` | empresa_delete | POST | redirect |
| `/usuarios/empresas/<pk>/sucursales` | sucursal_list | GET, POST | HTML / JSON |
| `/usuarios/sucursales/editar/<pk>/`, `/usuarios/sucursales/eliminar/<pk>/` | sucursal_edit, sucursal_delete | | JSON |
| `/usuarios/cambiar-empresa/<id>/` | cambiar_empresa | GET | redirect |
| `/categorias/nueva_categoria/` | nueva_categoria | POST | JSON |
| `/categorias/lista_categorias/` | lista_categorias | GET | HTML |
| `/categorias/editar/<pk>/`, `/categorias/eliminar/<pk>/` | editar_categoria, eliminar_categoria | GET/POST | JSON |
| `/categorias/<pk>/nueva_subcategoria/`, `/categorias/<pk>/lista_subcategorias/` | | | |
| `/categorias/subcategorias/editar/<pk>/`, `/categorias/subcategorias/eliminar/<pk>/` | | | |
| `/categorias/subcategorias/<pk>/nueva_clase/`, `/categorias/subcategorias/<pk>/lista_clases/` | | | |
| `/categorias/clases/editar/<pk>/`, `/categorias/clases/eliminar/<pk>/` | | | |
| `/productos/nuevo/` | crear_producto | GET, POST | HTML |
| `/productos/lista_productos/` | lista_productos | GET; `?draw=` → DataTables server-side | HTML / JSON |
| `/productos/busqueda/?q=&categoria=` | busqueda_producto | GET | HTML |
| `/productos/editar/<pk>/` | editar_producto | GET, POST | HTML |
| `/productos/desactivar/<pk>/`, `/productos/activar/<pk>/` | | POST | redirect |
| `/productos/bsq_por_codigo/?codigo=` | bsq_por_codigo | GET | JSON |
| `/productos/obtener_modelos/` | obtener_modelos_unicos | GET | JSON (lista) |
| `/inventario/movimiento_inventario/` | movimiento_inventario | GET, POST (multipart) | HTML |
| `/inventario/traslado/iniciar/` | iniciar_traslado | GET, POST (multipart) | HTML |
| `/inventario/traslados_pendientes/` | traslados_pendientes | GET | HTML |
| `/inventario/traslado/confirmar/<pk>/` | confirmar_traslado | GET, POST | HTML |
| `/inventario/producto_movimientos/`, `/inventario/sucursal_movimientos/` | movimientos_por_producto / _sucursal | GET, POST (selector) | HTML |
| `/inventario/empresa_movimientos/` | movimientos_por_empresa | GET | HTML |
| `/reportes/reporte_diario/`, `/reportes/inventario_valorizado/` | | GET | HTML imprimible |
| `/reportes/carga_masiva/` | carga_masiva_productos | GET, POST (`archivo_excel`) | HTML |
| `/reportes/descargar_plantilla/` | descargar_plantilla_productos | GET | XLSX |
| `/static/…`, `/media/…` | `django.conf.urls.static` | | solo con `DEBUG=1` |

---

## 5. Configuración

`inv_manaudi/inv_manaudi/settings.py` lee variables de entorno (ver `.env.example`);
sin ellas usa valores de desarrollo.

| Variable | Default | Uso |
|---|---|---|
| `DJANGO_SECRET_KEY` | clave insegura de desarrollo | **Cambiar en producción** |
| `DJANGO_DEBUG` | `1` | `0` en producción |
| `DJANGO_ALLOWED_HOSTS` | `sifcol.pythonanywhere.com,localhost,127.0.0.1` | separados por coma |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://sifcol.pythonanywhere.com` | Django 4 exige esquema |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | `inv_manaudi`, `root`, `f4d3s2a1`, `localhost`, `3306` | En Docker `DB_HOST=db` se fuerza desde compose |
| `RUN_MIGRATIONS` | `1` | El entrypoint corre `migrate` al arrancar |
| `WEB_HOST_PORT`, `DB_HOST_PORT` | `8012`, `3307` | Puertos publicados en el host (solo 127.0.0.1) |

Otros ajustes: `LANGUAGE_CODE='es-ec'`, `TIME_ZONE='America/Guayaquil'`, `USE_TZ=True`
(las fechas se guardan en UTC y se muestran en hora local), `USE_THOUSAND_SEPARATOR=True`,
`STATIC_ROOT=inv_manaudi/staticfiles/` (para `collectstatic`), `MEDIA_ROOT=inv_manaudi/media/`
(en Docker, volumen `media_data`), `LOGIN_URL='login'`.

---

## 6. Entorno de desarrollo (Docker)

- `docker-compose.yml`: servicio `db` (mysql:8.0, utf8mb4, `mysql_native_password`,
  volumen `db_data`, importa `docker/dumps/*.sql` al crear el volumen) y servicio `web`
  (build del `Dockerfile`, monta `./inv_manaudi` en `/app`, volumen `media_data`,
  `env_file: .env`).
- `docker/entrypoint.sh`: espera a MySQL con PyMySQL, corre `migrate` y ejecuta el CMD
  (`runserver 0.0.0.0:8000`).
- El código se recarga en caliente (volumen montado). Tras cambiar `requirements.txt`:
  `docker compose build`.
- No hay entorno virtual local: ejecutar siempre `manage.py` dentro del contenedor.

### Comandos de gestión propios

| Comando | Qué hace |
|---|---|
| `populate_data [--clear] [--empresas N]` | Grupos, empresas, sucursales, usuarios (clave 1234), clasificación, 10 productos por empresa, stock inicial aleatorio y pocos movimientos. `--clear` borra todo menos superusuarios. |
| `populate_demo [--force] [--seed N]` | Sobre lo anterior: códigos auxiliares/EAN, un producto inactivo por empresa, 30 días de movimientos, traslados confirmados (uno con faltante) y pendientes, alertas de stock bajo y un agotado, movimientos de hoy. Idempotente salvo `--force`. Documentos `DEMO-*`. |

### Pruebas

No hay pruebas automatizadas (los `tests.py` están vacíos). Para una verificación rápida
tras un cambio: `manage.py check`, `makemigrations --check --dry-run` y recorrer las
pantallas con cada usuario de prueba.

---

## 7. Producción (PythonAnywhere)

Estado actual: `https://sifcol.pythonanywhere.com`, base `sifcol$inv_manaudi`.

Pasos de despliegue de una nueva versión:

1. Verificar que la cuenta use **Python ≥ 3.8** (Django 4.2 lo exige; la imagen Docker usa 3.10).
2. Subir el código (git pull o upload) y `pip install -r requirements.txt` en el virtualenv de la web app.
3. Definir las variables de entorno en el archivo WSGI o en `.env` cargado desde él:
   `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`,
   `DB_NAME=sifcol$inv_manaudi`, `DB_USER=sifcol`, `DB_PASSWORD`, `DB_HOST=sifcol.mysql.pythonanywhere-services.com`.
4. `python manage.py migrate` y `python manage.py collectstatic` (mapear `/static/` →
   `inv_manaudi/staticfiles/` y `/media/` → `inv_manaudi/media/` en la pestaña Web).
5. Recargar la web app.

Respaldo de producción y carga en Docker: ver `docker/dumps/README.md`.

---

## 8. Mantenimiento habitual

| Tarea | Cómo |
|---|---|
| Crear usuario | `/admin/` → Usuarios (grupos) → Perfiles de usuario (empresa, sucursal). |
| Cambiar contraseña | `/admin/` → Usuarios → usuario → enlace de contraseña, o `manage.py changepassword`. |
| Nueva empresa | Manaudi: Manejo Empresas → crear; luego sus sucursales y usuarios. |
| Corregir stock | Registrar un movimiento contrario (no editar `Inventario` a mano salvo emergencia). |
| Respaldo | `mysqldump` (ver README). Los adjuntos están en `media/documento_soporte/`. |
| Logs | Django no tiene logging configurado; en Docker `docker compose logs web`; en PythonAnywhere los archivos de error/server log. |

---

## 9. Limitaciones conocidas y mejoras sugeridas

Comportamientos actuales que conviene conocer (no son errores, son decisiones o faltantes):

1. **Sin pruebas automatizadas.** Prioridad alta para cualquier evolución.
2. **Movimientos inmutables.** No hay anulación; se corrige con movimientos contrarios.
3. **Origen del traslado libre.** Un encargado puede iniciar un traslado desde cualquier
   sucursal de su empresa; solo la confirmación está restringida a su sucursal.
4. **Stock inicial sin movimiento.** La carga masiva y `populate_data` fijan saldos
   directamente; el kardex no los muestra.
5. **Login**: la casilla "Recuérdame" y el enlace "solicitar usuario" no hacen nada; un
   login fallido no muestra mensaje de error.
6. **Dashboard**: los enlaces "Ver detalle" de las tarjetas no llevan a ningún lado.
7. **Reportes solo HTML**: se imprimen desde el navegador; no hay exportación a Excel/PDF
   (salvo la lista de productos vía DataTables).
8. **Sin logging ni auditoría** más allá de `usuario` y `fecha` en movimientos y traslados.
9. **Credenciales por defecto en `settings.py`** para desarrollo; en producción deben
   venir del entorno.
10. **CDN**: las pantallas de alta/edición de producto cargan Select2 y jQuery Mask desde
    internet; sin conexión esos selectores pierden estilo.

Mejoras sugeridas: pruebas unitarias e integración; anulación controlada de movimientos;
restringir el origen de traslados a la sucursal del usuario; exportar reportes; logging;
API REST (DRF) si se requiere integración con otros sistemas; respaldos automáticos.

---

## 10. Historial de cambios recientes

- **18/10/2026**: contenerización con Docker, regeneración de migraciones, corrección de
  bugs de permisos e integridad de stock (transacciones + `select_for_update`),
  actualización de Django 3.2.25 → 4.2.30, variables de entorno.
- **24/10/2026**: documentación completa (docstrings, README, manuales), comando
  `populate_demo`, correcciones menores: tipo de sucursal en el formulario de sucursales,
  cantidad en la tabla de traslados pendientes, encabezado faltante en traslados recientes,
  dashboard limitado a 10 movimientos, formulario de movimientos usa la empresa activa
  (superusuario), movimientos por empresa/sucursal restringidos a Supervisor (como el
  menú), botón editar oculto para Auditor en la lista de productos, carga masiva tolera
  celdas vacías y solo acepta `.xlsx`; eliminados archivos huérfanos
  (`populate_pythonanywhere.py`, `productos_sucursal.html`, `inventario/signals.py`).
