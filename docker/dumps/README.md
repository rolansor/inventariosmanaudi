# Dumps de base de datos

Los archivos `.sql` y `.sql.gz` de esta carpeta están ignorados en git (solo se versiona este README).

## Importación automática

Cualquier archivo `.sql` o `.sql.gz` colocado aquí se importa automáticamente la **primera vez**
que se crea el volumen de MySQL (`docker compose up`). Si el volumen ya existe, hay que recrearlo:

```bash
docker compose down -v          # borra el volumen db_data (y media_data)
docker compose up -d
```

## Importar un dump de producción (PythonAnywhere)

1. Exportar desde una consola de PythonAnywhere:

   ```bash
   mysqldump -u sifcol -h sifcol.mysql.pythonanywhere-services.com -p 'sifcol$inv_manaudi' > inv_manaudi_prod.sql
   ```

2. Revisar que el dump no contenga `CREATE DATABASE` ni `USE \`sifcol$inv_manaudi\``.
   Si los tiene, eliminarlos o cambiar el nombre por `inv_manaudi`.

3. Copiar el archivo a esta carpeta e importarlo (con el contenedor ya levantado):

   ```bash
   docker compose exec -T db mysql -uroot -pf4d3s2a1 inv_manaudi < docker/dumps/inv_manaudi_prod.sql
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py showmigrations
   ```

   Las migraciones del repo tienen los mismos nombres que las que se aplicaron en producción,
   por lo que Django las dará por aplicadas. Si el esquema de producción fuera anterior a algún
   campo de los modelos (por ejemplo `productos_producto.modelo`), `migrate` no lo creará:
   comparar con `docker compose exec web python manage.py sqlmigrate productos 0001_initial`
   y agregar la columna a mano.

4. Los usuarios de producción conservan sus contraseñas. `populate_data --clear` borraría
   todos esos datos: no usarlo sobre una base con datos reales.

## Exportar la base del contenedor

```bash
docker compose exec db mysqldump -uroot -pf4d3s2a1 inv_manaudi > docker/dumps/backup.sql
```
