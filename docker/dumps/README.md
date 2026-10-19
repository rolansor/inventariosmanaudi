# Dumps de base de datos

Cualquier archivo `.sql` o `.sql.gz` colocado en esta carpeta se importa automáticamente
la **primera vez** que se crea el volumen de MySQL (`docker compose up`).

Si la base ya fue creada y se quiere importar un dump después:

```bash
docker compose exec -T db mysql -uroot -p"$DB_PASSWORD" inv_manaudi < docker/dumps/archivo.sql
```

Para exportar la base actual del contenedor:

```bash
docker compose exec db mysqldump -uroot -p"$DB_PASSWORD" inv_manaudi > docker/dumps/backup.sql
```
