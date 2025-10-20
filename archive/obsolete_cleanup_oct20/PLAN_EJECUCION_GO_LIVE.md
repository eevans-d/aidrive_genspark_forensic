## Plan de Ejecución Go-Live Dashboard (Bloqueado)

Este plan ha sido aprobado y NO debe alterarse salvo defectos críticos. Cada paso tiene un único ciclo de implementación (+1 corrección si falla). Mejoras extra pasan a Backlog Diferido.

### Secuencia de Pasos
1. Cobertura: badge real automatizado.
2. Subir umbral cobertura a 85%.
3. Auditoría superficie seguridad (rutas / headers).
4. Validación real secretos Staging.
5. Primer despliegue Staging + validaciones.
6. Simulación rollback Staging.
7. Release semántico inicial (tag v1.x).
8. Baseline rendimiento (latencias p50/p95, memoria).
9. Quick wins performance (máx 2; condicional >500ms p95).
10. Retiro filtro pytest (o aplazamiento formal).
11. Cierre documentación operativa (consistencia).
12. Revisión observabilidad (logs/metrics campos esenciales).
13. Checklist Go-Live (hard freeze scope).
14. Despliegue Producción (tag) + verificación.
15. Post-mortem y freeze 7 días.

### Reglas Anti Ciclo Infinito
- Máx 1 iteración de refinamiento por paso.
- Cambios no críticos → Backlog Diferido.
- No se eleva cobertura >85% en esta fase.
- Performance: sólo si clara mejora >20% en métrica observada.
 - Tests de integraciones (AFIP/ML) excluidos temporalmente del alcance de cobertura; reintroducción fuera de este plan.

### Backlog Diferido (No ejecutar ahora)
- Cobertura >85%.
- SAST adicional (CodeQL/Semgrep).
- Rate limiting distribuido.
- Manifests Kubernetes / auto-escalado.
- CDN estáticos versionados hash.
- WAF / reglas avanzadas.
- Tracing distribuido (OpenTelemetry).
- Índices SQL avanzados y tuning fino.
- Métricas de negocio avanzadas / dashboards externos.

---
Marcado como 'locked' a fecha de creación. Cualquier desviación requiere aprobación explícita documentada aquí.
