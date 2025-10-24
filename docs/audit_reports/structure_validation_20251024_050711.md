# VALIDACIÓN DE ESTRUCTURA Y CONVENCIONES
Generado: 2025-10-24T05:07:11Z

✅ inventario-retail/ (con guión)
✅ web_dashboard/
✅ shared/ (configuración)
✅ CI/CD workflow

## Métricas Prometheus Existentes
❌ CRÍTICO: Métrica dashboard_request_duration_ms_p95 no encontrada
Buscando métricas alternativas...
inventario-retail/web_dashboard/dashboard_app.py:    lines.append("# HELP dashboard_request_duration_ms_sum Total duration by path (ms)")
inventario-retail/web_dashboard/dashboard_app.py:    lines.append("# TYPE dashboard_request_duration_ms_sum counter")
inventario-retail/web_dashboard/dashboard_app.py:        lines.append(f'dashboard_request_duration_ms_sum{{path="{p}"}} {data.get("total_duration_ms", 0)}')

## Convenciones de Importación
✅ Patrones sys.path.insert detectados
inventario-retail/venv/lib/python3.12/site-packages/setuptools/installer.py:        sys.path.insert(0, str(dist.locate_file('')))
inventario-retail/venv/lib/python3.12/site-packages/setuptools/build_meta.py:            sys.path.insert(0, script_dir)
inventario-retail/venv/lib/python3.12/site-packages/pip/__main__.py:    sys.path.insert(0, path)
