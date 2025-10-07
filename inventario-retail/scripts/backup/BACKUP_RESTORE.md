# Guía de Backup y Restauración - Mini Market

## Índice
- [Introducción](#introducción)
- [Estructura de Directorios](#estructura-de-directorios)
- [Scripts Disponibles](#scripts-disponibles)
- [Procedimiento de Backup](#procedimiento-de-backup)
  - [Backup de Base de Datos](#backup-de-base-de-datos)
  - [Backup de Volúmenes Docker](#backup-de-volúmenes-docker)
- [Procedimiento de Restauración](#procedimiento-de-restauración)
  - [Restauración de Base de Datos](#restauración-de-base-de-datos)
  - [Restauración de Volúmenes Docker](#restauración-de-volúmenes-docker)
- [Automatización](#automatización)
- [Políticas de Retención](#políticas-de-retención)
- [Verificación de Backups](#verificación-de-backups)
- [Escenarios de Recuperación](#escenarios-de-recuperación)
- [Preguntas Frecuentes](#preguntas-frecuentes)

## Introducción

Este documento describe los procedimientos de backup y restauración para el sistema Mini Market. Estos procedimientos son fundamentales para garantizar la disponibilidad de los datos y la continuidad del servicio en caso de fallas o incidentes.

Los scripts de backup y restauración han sido diseñados para ser robustos, informativos y flexibles, adaptándose a diferentes entornos (desarrollo, staging y producción) y permitiendo la recuperación completa del sistema en caso de ser necesario.

## Estructura de Directorios

```
inventario-retail/
├── backups/
│   ├── database/             # Backups de base de datos
│   └── volumes/              # Backups de volúmenes Docker
├── scripts/
│   └── backup/
│       ├── backup_database.sh        # Script de backup de base de datos
│       ├── backup_volumes.sh         # Script de backup de volúmenes
│       ├── restore_database.sh       # Script de restauración de base de datos
│       └── restore_volumes.sh        # Script de restauración de volúmenes
└── config/
    ├── backup_config.development.env  # Configuración para desarrollo
    ├── backup_config.staging.env      # Configuración para staging
    └── backup_config.production.env   # Configuración para producción
```

## Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `backup_database.sh` | Realiza un respaldo completo de la base de datos PostgreSQL, separando esquema y datos |
| `backup_volumes.sh` | Respalda los volúmenes Docker utilizados por los servicios |
| `restore_database.sh` | Restaura una base de datos PostgreSQL a partir de un backup |
| `restore_volumes.sh` | Restaura volúmenes Docker a partir de un backup |

## Procedimiento de Backup

### Backup de Base de Datos

El script `backup_database.sh` realiza un backup completo de la base de datos PostgreSQL. Los archivos se guardan en el directorio `backups/database/`.

**Características:**
- Separación de esquema y datos para mayor flexibilidad en la restauración
- Compresión automática de los archivos
- Generación de metadata con información del backup
- Políticas de retención configurables
- Soporte para diferentes entornos

**Uso:**
```bash
./backup_database.sh [entorno]
```

Donde `[entorno]` puede ser `development`, `staging` o `production` (por defecto: `development`).

**Ejemplo:**
```bash
./backup_database.sh production
```

**Resultado:**
- Archivos generados:
  - `database_production_YYYYMMDD_HHMMSS.tar.gz` (archivo comprimido)
  - `database_production_YYYYMMDD_HHMMSS_metadata.json` (metadata)

### Backup de Volúmenes Docker

El script `backup_volumes.sh` realiza un backup de los volúmenes Docker utilizados por los servicios. Los archivos se guardan en el directorio `backups/volumes/`.

**Volúmenes respaldados:**
- `inventario-retail_postgres-data` (datos de PostgreSQL)
- `inventario-retail_grafana-data` (configuración y datos de Grafana)
- `inventario-retail_prometheus-data` (datos históricos de métricas)
- `inventario-retail_loki-data` (logs almacenados)
- `inventario-retail_redis-data` (datos de caché)

**Uso:**
```bash
./backup_volumes.sh [entorno]
```

**Ejemplo:**
```bash
./backup_volumes.sh production
```

**Resultado:**
- Archivos generados:
  - `volumes_production_YYYYMMDD_HHMMSS.tar.gz` (archivo comprimido)
  - `volumes_production_YYYYMMDD_HHMMSS_metadata.json` (metadata)

## Procedimiento de Restauración

### Restauración de Base de Datos

El script `restore_database.sh` restaura una base de datos PostgreSQL a partir de un backup.

**Características:**
- Verificación de conexión a PostgreSQL
- Recreación completa de la base de datos
- Restauración de esquema y datos
- Verificación de la restauración

**Uso:**
```bash
./restore_database.sh [archivo_backup] [entorno]
```

**Ejemplo:**
```bash
./restore_database.sh /ruta/al/backup/database_production_20251007_120000.tar.gz production
```

**IMPORTANTE:** Este proceso eliminará la base de datos existente y todos sus datos antes de restaurar el backup.

### Restauración de Volúmenes Docker

El script `restore_volumes.sh` restaura volúmenes Docker a partir de un backup.

**Características:**
- Restauración de volúmenes existentes o creación de nuevos si no existen
- Verificación del proceso de restauración
- Informe detallado de volúmenes restaurados

**Uso:**
```bash
./restore_volumes.sh [archivo_backup] [entorno]
```

**Ejemplo:**
```bash
./restore_volumes.sh /ruta/al/backup/volumes_production_20251007_120000.tar.gz production
```

**IMPORTANTE:** Este proceso sobrescribirá los datos de los volúmenes existentes. Asegúrese de que los servicios que utilizan estos volúmenes estén detenidos antes de la restauración.

## Automatización

Se recomienda configurar tareas programadas (cron jobs) para ejecutar los scripts de backup regularmente:

**Ejemplo de configuración cron:**

```
# Backup diario de base de datos (a las 2 AM)
0 2 * * * cd /ruta/a/inventario-retail/scripts/backup && ./backup_database.sh production >> /var/log/minimarket_backup_db.log 2>&1

# Backup semanal de volúmenes (domingo a las 3 AM)
0 3 * * 0 cd /ruta/a/inventario-retail/scripts/backup && ./backup_volumes.sh production >> /var/log/minimarket_backup_vol.log 2>&1
```

## Políticas de Retención

Los scripts de backup implementan una política de retención configurable para controlar el espacio de almacenamiento:

- Por defecto, los backups más antiguos de 30 días son eliminados automáticamente
- Este valor puede ajustarse modificando la variable `RETENTION_DAYS` en cada script
- Para retener backups permanentemente, deben moverse manualmente a una ubicación diferente

## Verificación de Backups

Es importante verificar regularmente la integridad de los backups:

1. **Para bases de datos:**
   - Restaurar el backup en un entorno de prueba
   - Verificar la estructura y datos de tablas críticas
   - Ejecutar consultas de prueba para validar la integridad

2. **Para volúmenes:**
   - Restaurar los volúmenes en un entorno de prueba
   - Iniciar los servicios y verificar su funcionamiento
   - Validar acceso a datos críticos a través de las interfaces de usuario

## Escenarios de Recuperación

### Escenario 1: Recuperación de la base de datos

1. Detenga los servicios que acceden a la base de datos:
   ```bash
   docker-compose -f docker-compose.production.yml stop agente_deposito agente_negocio dashboard
   ```

2. Restaure la base de datos:
   ```bash
   ./restore_database.sh /ruta/al/backup/database_production_[fecha].tar.gz production
   ```

3. Reinicie los servicios:
   ```bash
   docker-compose -f docker-compose.production.yml up -d agente_deposito agente_negocio dashboard
   ```

### Escenario 2: Recuperación completa del sistema

1. Detenga todos los servicios:
   ```bash
   docker-compose -f docker-compose.production.yml down
   ```

2. Restaure la base de datos:
   ```bash
   ./restore_database.sh /ruta/al/backup/database_production_[fecha].tar.gz production
   ```

3. Restaure los volúmenes:
   ```bash
   ./restore_volumes.sh /ruta/al/backup/volumes_production_[fecha].tar.gz production
   ```

4. Inicie todos los servicios:
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```

## Preguntas Frecuentes

### ¿Con qué frecuencia deben realizarse los backups?

- Base de datos: Diariamente (para entornos de producción)
- Volúmenes: Semanalmente o después de cambios importantes en la configuración

### ¿Dónde deben almacenarse los backups?

Los backups deben almacenarse en al menos dos ubicaciones diferentes:
1. Localmente en el servidor (para recuperación rápida)
2. En un almacenamiento externo o en la nube (para recuperación ante desastres)

### ¿Qué hacer si falla la restauración?

1. Verifique los logs de error del script
2. Asegúrese de que PostgreSQL esté en ejecución y accesible
3. Verifique que los servicios que utilizan los recursos estén detenidos
4. Valide que el archivo de backup sea válido y no esté corrupto
5. Consulte los metadatos del backup para verificar su origen y contenido

### ¿Cómo verificar que un backup es válido?

Realice restauraciones de prueba periódicas en un entorno aislado para validar que los backups son recuperables y contienen los datos esperados.

---

## Información Adicional

- Los scripts generan logs detallados durante su ejecución
- Cada backup incluye un archivo de metadatos con información relevante sobre su contenido
- Se recomienda realizar pruebas de restauración periódicas para validar los procedimientos