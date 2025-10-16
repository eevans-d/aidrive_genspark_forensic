# Load Testing Results

Este directorio contiene los resultados de las ejecuciones de load testing.

## Estructura

```
results/
├── test-health-YYYYMMDD_HHMMSS.log          # Logs de ejecución
├── test-inventory-read-YYYYMMDD_HHMMSS.log
├── test-inventory-write-YYYYMMDD_HHMMSS.log
├── test-metrics-YYYYMMDD_HHMMSS.log
├── health-check-summary.json                 # Datos raw JSON
├── inventory-read-summary.json
├── inventory-write-summary.json
├── metrics-summary.json
└── consolidated-report-YYYYMMDD_HHMMSS.txt  # Reporte consolidado
```

## Limpieza

Los archivos antiguos pueden ser eliminados manualmente:

```bash
# Eliminar resultados más antiguos de 30 días
find results/ -name "*.log" -mtime +30 -delete
find results/ -name "*.json" -mtime +30 -delete
find results/ -name "*.txt" -mtime +30 -delete
```

## Retención

- **Development:** 7 días
- **Staging:** 30 días
- **Production:** 90 días (considerar mover a S3/GCS para long-term storage)

## Análisis

Ver [LOAD_TESTING.md](../LOAD_TESTING.md) para guías de análisis de resultados.
