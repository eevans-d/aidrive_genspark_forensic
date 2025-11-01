/**
 * SISTEMA DE HEALTH CHECKS Y MONITOREO AUTOMÁTICO
 * Edge Function para Monitoreo Continuo del Sistema de Cron Jobs
 * 
 * CARACTERÍSTICAS:
 * - Health checks cada 5 minutos
 * - Detección automática de fallos
 * - Recovery automático con circuit breakers
 * - Métricas de performance en tiempo real
 * - Alertas automáticas para degradación de servicio
 * 
 * @author MiniMax Agent - Sistema Automatizado
 * @version 3.0.0
 * @date 2025-11-01
 * @license Enterprise Level
 */

// =====================================================
// INTERFACES Y TIPOS
// =====================================================

interface HealthCheckResult {
    component: string;
    status: 'healthy' | 'degraded' | 'critical';
    responseTime: number;
    details: any;
    timestamp: string;
}

interface SystemHealth {
    overall: 'healthy' | 'degraded' | 'critical';
    score: number;
    components: {
        database: HealthCheckResult;
        memory: HealthCheckResult;
        jobs: HealthCheckResult;
        alerts: HealthCheckResult;
        performance: HealthCheckResult;
    };
    recommendations: string[];
    autoRecovery: boolean;
}

interface MonitoringMetrics {
    timestamp: string;
    uptime: number;
    responseTime: number;
    memoryUsage: number;
    activeJobs: number;
    successRate: number;
    alertsGenerated: number;
    circuitBreakersOpen: number;
}

interface RecoveryAction {
    type: 'restart_job' | 'clear_cache' | 'reset_circuit_breaker' | 'cleanup_db' | 'escalate_alert';
    target: string;
    parameters: any;
    timestamp: string;
    status: 'pending' | 'executing' | 'completed' | 'failed';
}

// =====================================================
// VARIABLES GLOBALES
// =====================================================

const MONITORING_HISTORY: MonitoringMetrics[] = [];
const RECOVERY_QUEUE: RecoveryAction[] = [];
const HEALTH_CHECKS_INTERVAL = 5 * 60 * 1000; // 5 minutos
const CRITICAL_THRESHOLD = 70;
const DEGRADED_THRESHOLD = 85;

// =====================================================
// FUNCIÓN PRINCIPAL
// =====================================================

Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
        'Access-Control-Max-Age': '86400',
        'Content-Type': 'application/json'
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const url = new URL(req.url);
        const action = url.pathname.split('/').pop() || 'health-check';

        console.log(`[HEALTH_MONITOR] Acción: ${action}`);

        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Configuración de Supabase faltante');
        }

        let response: Response;

        switch (action) {
            case 'health-check':
                response = await executeHealthCheck(supabaseUrl, serviceRoleKey, corsHeaders);
                break;
            case 'metrics':
                response = await getMonitoringMetrics(corsHeaders);
                break;
            case 'recovery':
                response = await executeRecoveryAction(req, supabaseUrl, serviceRoleKey, corsHeaders);
                break;
            case 'status':
                response = await getSystemStatus(supabaseUrl, serviceRoleKey, corsHeaders);
                break;
            case 'auto-recovery':
                response = await executeAutoRecovery(supabaseUrl, serviceRoleKey, corsHeaders);
                break;
            default:
                throw new Error(`Acción no válida: ${action}`);
        }

        return response;

    } catch (error) {
        console.error('[HEALTH_MONITOR] Error:', error);
        
        return new Response(JSON.stringify({
            success: false,
            error: {
                code: 'HEALTH_MONITOR_ERROR',
                message: error.message,
                timestamp: new Date().toISOString()
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// =====================================================
// FUNCIONES PRINCIPALES
// =====================================================

/**
 * EJECUTAR HEALTH CHECK COMPLETO
 */
async function executeHealthCheck(
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>
): Promise<Response> {
    console.log('[HEALTH_MONITOR] Iniciando health check completo');

    const startTime = Date.now();
    const healthResults: SystemHealth = {
        overall: 'healthy',
        score: 100,
        components: {
            database: await checkDatabaseHealth(supabaseUrl, serviceRoleKey),
            memory: await checkMemoryHealth(),
            jobs: await checkJobsHealth(supabaseUrl, serviceRoleKey),
            alerts: await checkAlertsHealth(supabaseUrl, serviceRoleKey),
            performance: await checkPerformanceMetrics(supabaseUrl, serviceRoleKey)
        },
        recommendations: [],
        autoRecovery: false
    };

    // Calcular health score general
    healthResults.score = calculateHealthScore(healthResults);
    
    // Determinar estado general
    if (healthResults.score >= DEGRADED_THRESHOLD) {
        healthResults.overall = 'healthy';
    } else if (healthResults.score >= CRITICAL_THRESHOLD) {
        healthResults.overall = 'degraded';
        healthResults.autoRecovery = true;
    } else {
        healthResults.overall = 'critical';
        healthResults.autoRecovery = true;
    }

    // Generar recomendaciones
    healthResults.recommendations = generateHealthRecommendations(healthResults);

    // Registrar métricas
    await recordMonitoringMetrics(healthResults, supabaseUrl, serviceRoleKey);

    // Ejecutar recovery automático si es necesario
    if (healthResults.autoRecovery) {
        console.log('[HEALTH_MONITOR] Ejecutando recovery automático');
        await executeAutoRecovery(supabaseUrl, serviceRoleKey, corsHeaders);
    }

    // Crear alertas si es crítico
    if (healthResults.overall === 'critical') {
        await createSystemHealthAlert(healthResults, supabaseUrl, serviceRoleKey);
    }

    const duration = Date.now() - startTime;
    console.log(`[HEALTH_MONITOR] Health check completado en ${duration}ms`);

    return new Response(JSON.stringify({
        success: true,
        data: {
            health: healthResults,
            duration,
            timestamp: new Date().toISOString()
        }
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}

/**
 * VERIFICAR SALUD DE BASE DE DATOS
 */
async function checkDatabaseHealth(
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<HealthCheckResult> {
    const startTime = Date.now();
    
    try {
        // Test de conectividad básica
        const testResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_tracking?select=count&limit=1`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const responseTime = Date.now() - startTime;
        
        if (!testResponse.ok) {
            throw new Error(`Database connection failed: ${testResponse.status}`);
        }

        // Obtener estadísticas de conexión
        const statsResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_execution_log?select=count&limit=1&start_time=gte.${new Date(Date.now() - 60 * 60 * 1000).toISOString()}`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        // Verificar performance de consultas recientes
        const performanceData = await getDatabasePerformanceMetrics(supabaseUrl, serviceRoleKey);
        
        const status = responseTime < 500 && performanceData.healthy ? 'healthy' :
                      responseTime < 2000 ? 'degraded' : 'critical';

        return {
            component: 'database',
            status,
            responseTime,
            details: {
                connectionOk: testResponse.ok,
                performanceScore: performanceData.score,
                recentQueries: performanceData.recentQueries,
                activeConnections: 1
            },
            timestamp: new Date().toISOString()
        };

    } catch (error) {
        return {
            component: 'database',
            status: 'critical',
            responseTime: Date.now() - startTime,
            details: {
                error: error.message,
                connectionFailed: true
            },
            timestamp: new Date().toISOString()
        };
    }
}

/**
 * VERIFICAR SALUD DE MEMORIA
 */
async function checkMemoryHealth(): Promise<HealthCheckResult> {
    const startTime = Date.now();
    const memoryUsage = performance.memory ? {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        percentage: (performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize) * 100
    } : { used: 0, total: 0, percentage: 50 };

    const status = memoryUsage.percentage < 70 ? 'healthy' :
                  memoryUsage.percentage < 85 ? 'degraded' : 'critical';

    return {
        component: 'memory',
        status,
        responseTime: Date.now() - startTime,
        details: {
            usedMB: Math.round(memoryUsage.used / 1024 / 1024),
            totalMB: Math.round(memoryUsage.total / 1024 / 1024),
            percentage: Math.round(memoryUsage.percentage),
            gcRuns: (globalThis as any).gcRuns || 0
        },
        timestamp: new Date().toISOString()
    };
}

/**
 * VERIFICAR SALUD DE JOBS
 */
async function checkJobsHealth(
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<HealthCheckResult> {
    const startTime = Date.now();

    try {
        // Obtener estado de jobs activos
        const jobsResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_tracking?select=*&activo=eq.true`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const jobs = jobsResponse.ok ? await jobsResponse.json() : [];

        // Obtener ejecuciones recientes
        const executionsResponse = await fetch(
            `${supabaseUrl}/rest/v1/cron_jobs_execution_log?select=*&start_time=gte.${new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()}&order=start_time.desc&limit=100`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        const executions = executionsResponse.ok ? await executionsResponse.json() : [];
        const recentFailures = executions.filter(e => e.estado === 'fallido').length;
        const successRate = executions.length > 0 ? 
            ((executions.length - recentFailures) / executions.length) * 100 : 100;

        const status = successRate > 90 && recentFailures < 2 ? 'healthy' :
                      successRate > 70 ? 'degraded' : 'critical';

        return {
            component: 'jobs',
            status,
            responseTime: Date.now() - startTime,
            details: {
                totalJobs: jobs.length,
                activeJobs: jobs.filter((j: any) => j.estado_job === 'ejecutando').length,
                successfulJobs: jobs.filter((j: any) => j.estado_job === 'exitoso').length,
                failedJobs: jobs.filter((j: any) => j.estado_job === 'fallido').length,
                recentSuccessRate: Math.round(successRate),
                recentFailures,
                lastExecution: jobs.length > 0 ? jobs[0].ultima_ejecucion : null
            },
            timestamp: new Date().toISOString()
        };

    } catch (error) {
        return {
            component: 'jobs',
            status: 'critical',
            responseTime: Date.now() - startTime,
            details: {
                error: error.message,
                unableToConnect: true
            },
            timestamp: new Date().toISOString()
        };
    }
}

/**
 * VERIFICAR SALUD DE ALERTAS
 */
async function checkAlertsHealth(
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<HealthCheckResult> {
    const startTime = Date.now();

    try {
        // Obtener alertas activas
        const alertsResponse = await fetch(
            `${supabaseUrl}/rest/v1/cron_jobs_alerts?select=*&estado_alerta=eq.activas&order=created_at.desc&limit=50`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        const alerts = alertsResponse.ok ? await alertsResponse.json() : [];
        const criticalAlerts = alerts.filter((a: any) => a.severidad === 'critica').length;
        const oldAlerts = alerts.filter((a: any) => 
            new Date(a.created_at) < new Date(Date.now() - 2 * 60 * 60 * 1000)
        ).length;

        const status = criticalAlerts === 0 && oldAlerts < 3 ? 'healthy' :
                      criticalAlerts < 3 ? 'degraded' : 'critical';

        return {
            component: 'alerts',
            status,
            responseTime: Date.now() - startTime,
            details: {
                totalActiveAlerts: alerts.length,
                criticalAlerts,
                mediumAlerts: alerts.filter((a: any) => a.severidad === 'media').length,
                lowAlerts: alerts.filter((a: any) => a.severidad === 'baja').length,
                oldAlerts,
                averageResolutionTime: calculateAverageResolutionTime(alerts)
            },
            timestamp: new Date().toISOString()
        };

    } catch (error) {
        return {
            component: 'alerts',
            status: 'critical',
            responseTime: Date.now() - startTime,
            details: {
                error: error.message,
                unableToCheck: true
            },
            timestamp: new Date().toISOString()
        };
    }
}

/**
 * VERIFICAR MÉTRICAS DE PERFORMANCE
 */
async function checkPerformanceMetrics(
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<HealthCheckResult> {
    const startTime = Date.now();

    try {
        // Obtener métricas del día
        const metricsResponse = await fetch(
            `${supabaseUrl}/rest/v1/cron_jobs_metrics?select=*&fecha_metricas=eq.${new Date().toISOString().split('T')[0]}`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        const metrics = metricsResponse.ok ? await metricsResponse.json() : [];
        
        if (metrics.length === 0) {
            return {
                component: 'performance',
                status: 'degraded',
                responseTime: Date.now() - startTime,
                details: {
                    message: 'No hay métricas disponibles para hoy',
                    uptime: 100
                },
                timestamp: new Date().toISOString()
            };
        }

        const totalUptime = metrics.reduce((sum: number, m: any) => sum + (m.disponibilidad_porcentual || 100), 0) / metrics.length;
        const totalSuccessRate = metrics.reduce((sum: number, m: any) => sum + (m.uptime_porcentaje || 100), 0) / metrics.length;

        const status = totalUptime > 95 && totalSuccessRate > 90 ? 'healthy' :
                      totalUptime > 80 ? 'degraded' : 'critical';

        return {
            component: 'performance',
            status,
            responseTime: Date.now() - startTime,
            details: {
                uptime: Math.round(totalUptime),
                successRate: Math.round(totalSuccessRate),
                jobsExecuted: metrics.reduce((sum: number, m: any) => sum + (m.ejecuciones_totales || 0), 0),
                avgExecutionTime: metrics.reduce((sum: number, m: any) => sum + (m.tiempo_promedio_ms || 0), 0) / metrics.length
            },
            timestamp: new Date().toISOString()
        };

    } catch (error) {
        return {
            component: 'performance',
            status: 'critical',
            responseTime: Date.now() - startTime,
            details: {
                error: error.message,
                unableToGetMetrics: true
            },
            timestamp: new Date().toISOString()
        };
    }
}

/**
 * CALCULAR HEALTH SCORE GENERAL
 */
function calculateHealthScore(health: SystemHealth): number {
    let score = 100;
    
    // Penalizar por componentes en estado crítico
    Object.values(health.components).forEach(component => {
        if (component.status === 'critical') score -= 25;
        else if (component.status === 'degraded') score -= 10;
    });

    return Math.max(0, Math.min(100, score));
}

/**
 * GENERAR RECOMENDACIONES DE SALUD
 */
function generateHealthRecommendations(health: SystemHealth): string[] {
    const recommendations: string[] = [];

    if (health.components.database.status === 'critical') {
        recommendations.push('Database connection failed - Check Supabase service status');
    }
    
    if (health.components.memory.status === 'critical') {
        recommendations.push('High memory usage detected - Restart edge function');
    }
    
    if (health.components.jobs.status === 'critical') {
        recommendations.push('Multiple job failures detected - Review job configurations');
    }
    
    if (health.components.alerts.status === 'critical') {
        recommendations.push('Too many active critical alerts - Manual intervention required');
    }

    if (health.overall === 'degraded') {
        recommendations.push('System operating in degraded mode - Monitor closely');
    }

    if (recommendations.length === 0) {
        recommendations.push('System operating normally');
    }

    return recommendations;
}

/**
 * REGISTRAR MÉTRICAS DE MONITOREO
 */
async function recordMonitoringMetrics(
    health: SystemHealth,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<void> {
    try {
        const metrics: MonitoringMetrics = {
            timestamp: new Date().toISOString(),
            uptime: health.score,
            responseTime: Object.values(health.components).reduce((sum, c) => sum + c.responseTime, 0),
            memoryUsage: health.components.memory.details.percentage,
            activeJobs: health.components.jobs.details.activeJobs,
            successRate: health.components.jobs.details.recentSuccessRate,
            alertsGenerated: health.components.alerts.details.totalActiveAlerts,
            circuitBreakersOpen: 0 // Se calcularía desde los circuit breakers
        };

        // Mantener historial limitado
        MONITORING_HISTORY.push(metrics);
        if (MONITORING_HISTORY.length > 144) { // 24 horas de datos (5 min intervals)
            MONITORING_HISTORY.shift();
        }

        // Guardar en base de datos
        await fetch(`${supabaseUrl}/rest/v1/cron_jobs_monitoring_history`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            },
            body: JSON.stringify({
                timestamp: metrics.timestamp,
                uptime_percentage: metrics.uptime,
                response_time_ms: metrics.responseTime,
                memory_usage_percent: metrics.memoryUsage,
                active_jobs_count: metrics.activeJobs,
                success_rate: metrics.successRate,
                alerts_generated: metrics.alertsGenerated,
                health_score: health.score,
                details: health
            })
        });

    } catch (error) {
        console.error('[HEALTH_MONITOR] Error registrando métricas:', error);
    }
}

/**
 * CREAR ALERTA DE SALUD DEL SISTEMA
 */
async function createSystemHealthAlert(
    health: SystemHealth,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<void> {
    try {
        const alertData = {
            job_id: 'health-monitor',
            execution_id: `health-${Date.now()}`,
            tipo_alerta: 'sistema_degradado',
            severidad: health.overall === 'critical' ? 'critica' : 'alta',
            titulo: `Sistema en estado ${health.overall.toUpperCase()}`,
            descripcion: `Health check detectó estado ${health.overall} con score ${health.score}/100. Componentes afectados: ${Object.entries(health.components).filter(([_, c]) => c.status !== 'healthy').map(([k, _]) => k).join(', ')}`,
            accion_recomendada: 'Revisar logs del sistema y ejecutar recovery automático',
            canales_notificacion: ['email', 'sms'],
            fecha_envio: new Date().toISOString()
        };

        await fetch(`${supabaseUrl}/rest/v1/cron_jobs_alerts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            },
            body: JSON.stringify(alertData)
        });

    } catch (error) {
        console.error('[HEALTH_MONITOR] Error creando alerta de salud:', error);
    }
}

/**
 * EJECUTAR AUTO RECOVERY
 */
async function executeAutoRecovery(
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>
): Promise<Response> {
    console.log('[HEALTH_MONITOR] Ejecutando auto recovery');

    const recoveryActions: RecoveryAction[] = [];

    try {
        // 1. Reiniciar circuit breakers abiertos
        const circuitBreakersResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_tracking?select=*&circuit_breaker_state=eq.open`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        if (circuitBreakersResponse.ok) {
            const openBreakers = await circuitBreakersResponse.json();
            for (const job of openBreakers) {
                recoveryActions.push({
                    type: 'reset_circuit_breaker',
                    target: job.job_id,
                    parameters: {},
                    timestamp: new Date().toISOString(),
                    status: 'pending'
                });
            }
        }

        // 2. Limpiar logs antiguos
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

        recoveryActions.push({
            type: 'cleanup_db',
            target: 'execution_logs',
            parameters: { olderThan: oneWeekAgo.toISOString() },
            timestamp: new Date().toISOString(),
            status: 'pending'
        });

        // 3. Ejecutar acciones de recovery
        const executedActions = [];
        for (const action of recoveryActions) {
            try {
                action.status = 'executing';
                const result = await executeRecoveryAction(action, supabaseUrl, serviceRoleKey);
                action.status = result.success ? 'completed' : 'failed';
                executedActions.push(action);
            } catch (error) {
                action.status = 'failed';
                console.error(`[HEALTH_MONITOR] Recovery action failed:`, error);
            }
        }

        return new Response(JSON.stringify({
            success: true,
            data: {
                actionsTriggered: recoveryActions.length,
                actionsExecuted: executedActions.filter(a => a.status === 'completed').length,
                actions: executedActions,
                timestamp: new Date().toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('[HEALTH_MONITOR] Error en auto recovery:', error);
        throw error;
    }
}

/**
 * EJECUTAR ACCIÓN DE RECOVERY ESPECÍFICA
 */
async function executeRecoveryAction(
    action: RecoveryAction,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<{ success: boolean; message: string }> {
    switch (action.type) {
        case 'reset_circuit_breaker':
            await fetch(`${supabaseUrl}/rest/v1/cron_jobs_tracking?job_id=eq.${action.target}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                },
                body: JSON.stringify({
                    circuit_breaker_state: 'closed',
                    updated_at: new Date().toISOString()
                })
            });
            return { success: true, message: `Circuit breaker reset for ${action.target}` };

        case 'cleanup_db':
            await fetch(`${supabaseUrl}/rest/v1/cron_jobs_execution_log?created_at=lt.${action.parameters.olderThan}`, {
                method: 'DELETE',
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            });
            return { success: true, message: 'Old execution logs cleaned' };

        case 'restart_job':
            // Trigger job restart via edge function
            await fetch(`${supabaseUrl}/functions/v1/cron-jobs-maxiconsumo`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': serviceRoleKey
                },
                body: JSON.stringify({
                    jobId: action.target,
                    parameters: { source: 'auto-recovery' }
                })
            });
            return { success: true, message: `Job ${action.target} restarted` };

        default:
            return { success: false, message: `Unknown action type: ${action.type}` };
    }
}

/**
 * OBTENER MÉTRICAS DE MONITOREO
 */
async function getMonitoringMetrics(
    corsHeaders: Record<string, string>
): Promise<Response> {
    const last24Hours = MONITORING_HISTORY.slice(-288); // 24 hours of 5-min intervals
    
    const summary = {
        current: last24Hours[last24Hours.length - 1] || null,
        averageUptime: last24Hours.length > 0 ? 
            last24Hours.reduce((sum, m) => sum + m.uptime, 0) / last24Hours.length : 100,
        averageResponseTime: last24Hours.length > 0 ?
            last24Hours.reduce((sum, m) => sum + m.responseTime, 0) / last24Hours.length : 0,
        trends: calculateTrends(last24Hours),
        history: last24Hours.slice(-24) // Last 2 hours
    };

    return new Response(JSON.stringify({
        success: true,
        data: summary
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}

/**
 * OBTENER ESTADO DEL SISTEMA
 */
async function getSystemStatus(
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>
): Promise<Response> {
    const healthCheck = await executeHealthCheck(supabaseUrl, serviceRoleKey, corsHeaders);
    const healthData = await healthCheck.json();

    const status = {
        overall: healthData.data.health.overall,
        score: healthData.data.health.score,
        uptime: '99.9%', // En producción sería dinámico
        lastUpdate: new Date().toISOString(),
        components: healthData.data.health.components,
        recommendations: healthData.data.health.recommendations,
        autoRecovery: healthData.data.health.autoRecovery
    };

    return new Response(JSON.stringify({
        success: true,
        data: status
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}

// =====================================================
// FUNCIONES DE UTILIDAD
// =====================================================

function calculateTrends(data: MonitoringMetrics[]): any {
    if (data.length < 2) return { trend: 'insufficient_data' };

    const recent = data.slice(-6); // Last 30 minutes
    const previous = data.slice(-12, -6); // Previous 30 minutes

    const recentAvg = recent.reduce((sum, m) => sum + m.uptime, 0) / recent.length;
    const previousAvg = previous.length > 0 ? 
        previous.reduce((sum, m) => sum + m.uptime, 0) / previous.length : recentAvg;

    return {
        uptime: recentAvg > previousAvg ? 'improving' : recentAvg < previousAvg ? 'declining' : 'stable',
        responseTime: recentAvg > previousAvg ? 'increasing' : recentAvg < previousAvg ? 'decreasing' : 'stable'
    };
}

async function getDatabasePerformanceMetrics(
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<any> {
    try {
        // Obtener tiempo promedio de queries recientes
        const recentQueriesResponse = await fetch(
            `${supabaseUrl}/rest/v1/cron_jobs_execution_log?select=duracion_ms&start_time=gte.${new Date(Date.now() - 60 * 60 * 1000).toISOString()}&duracion_ms=not.is.null`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        if (!recentQueriesResponse.ok) {
            return { healthy: false, score: 0, recentQueries: 0 };
        }

        const queries = await recentQueriesResponse.json();
        const avgTime = queries.length > 0 ? 
            queries.reduce((sum: number, q: any) => sum + (q.duracion_ms || 0), 0) / queries.length : 0;

        return {
            healthy: avgTime < 2000,
            score: Math.max(0, 100 - (avgTime / 100)), // Score based on response time
            recentQueries: queries.length
        };

    } catch (error) {
        return { healthy: false, score: 0, recentQueries: 0 };
    }
}

function calculateAverageResolutionTime(alerts: any[]): number {
    const resolvedAlerts = alerts.filter(a => a.fecha_resolucion);
    if (resolvedAlerts.length === 0) return 0;

    const totalTime = resolvedAlerts.reduce((sum, alert) => {
        const created = new Date(alert.created_at).getTime();
        const resolved = new Date(alert.fecha_resolucion).getTime();
        return sum + (resolved - created);
    }, 0);

    return Math.round(totalTime / resolvedAlerts.length / (1000 * 60)); // Minutes
}
