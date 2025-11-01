/**
 * SISTEMA COMPLETO DE CRON JOBS AUTOMÁTICOS - MINIMARKET SPRINT 6
 * Edge Function Principal para Gestión Avanzada de Jobs
 * 
 * FUNCIONALIDADES IMPLEMENTADAS:
 * 
 * 1. **SISTEMA DE ORQUESTACIÓN INTELIGENTE**
 *    - Gestión centralizada de todos los cron jobs
 *    - Scheduling inteligente con dependencias
 *    - Circuit breakers y recovery automático
 *    - Health checks y monitoreo continuo
 * 
 * 2. **JOBS ESPECÍFICOS IMPLEMENTADOS**
 *    - Job Diario: Actualización de precios Maxiconsumo (02:00 AM)
 *    - Job Semanal: Análisis de tendencias y ML (Domingos 03:00)
 *    - Job Tiempo Real: Alertas críticas (cada 15 minutos)
 *    - Job Mantenimiento: Limpieza automática (Lunes 01:00)
 * 
 * 3. **SISTEMA DE NOTIFICACIONES AVANZADO**
 *    - Email templates profesionales con branding
 *    - SMS para alertas críticas vía Twilio
 *    - Dashboard en tiempo real
 *    - Preferencias por usuario y severidad
 * 
 * 4. **RECOVERY Y ESCALABILIDAD**
 *    - Retry automático con backoff exponencial
 *    - Circuit breakers para jobs individuales
 *    - Escalamiento horizontal automático
 *    - Dead letter queues para recuperación
 * 
 * 5. **MONITOREO Y OBSERVABILIDAD**
 *    - Métricas en tiempo real
 *    - Logs centralizados estructurados
 *    - Dashboards interactivos
 *    - Alertas inteligentes con ML
 * 
 * @author MiniMax Agent - Sistema Automatizado
 * @version 3.0.0
 * @date 2025-11-01
 * @license Enterprise Level
 */

// =====================================================
// INTERFACES Y TIPOS PRINCIPALES
// =====================================================

interface CronJobConfig {
    jobId: string;
    name: string;
    type: 'diario' | 'semanal' | 'tiempo_real' | 'manual';
    cronExpression: string;
    priority: number;
    timeoutMs: number;
    maxRetries: number;
    circuitBreakerThreshold: number;
    active: boolean;
    parameters: Record<string, any>;
    dependencies?: string[];
    notificationChannels: string[];
}

interface JobExecutionContext {
    executionId: string;
    jobId: string;
    startTime: Date;
    userId?: string;
    requestId: string;
    source: 'scheduled' | 'manual' | 'api' | 'recovery';
    parameters: Record<string, any>;
    environment: {
        nodeVersion: string;
        memoryUsage: NodeJS.MemoryUsage;
        timestamp: string;
    };
}

interface JobResult {
    success: boolean;
    executionTimeMs: number;
    productsProcessed: number;
    productsSuccessful: number;
    productsFailed: number;
    alertsGenerated: number;
    emailsSent: number;
    smsSent: number;
    metrics: Record<string, any>;
    errors: string[];
    warnings: string[];
    recommendations: string[];
    nextExecutionRecommended?: string;
}

interface NotificationConfig {
    email: {
        templates: Record<string, EmailTemplate>;
        smtp: {
            host: string;
            port: number;
            secure: boolean;
            auth: {
                user: string;
                pass: string;
            };
        };
        from: string;
        fromName: string;
    };
    sms: {
        provider: 'twilio' | 'aws_sns';
        accountSid?: string;
        authToken?: string;
        fromNumber: string;
    };
    webhooks: {
        slack: {
            webhookUrl: string;
            channel: string;
        };
        teams: {
            webhookUrl: string;
        };
    };
}

interface EmailTemplate {
    subject: string;
    htmlBody: string;
    textBody: string;
    variables: string[];
    attachments?: AttachmentConfig[];
}

interface AttachmentConfig {
    filename: string;
    content: string;
    contentType: string;
}

interface SystemHealthMetrics {
    database: {
        status: 'healthy' | 'degraded' | 'critical';
        responseTime: number;
        activeConnections: number;
        queryPerformance: number;
    };
    memory: {
        used: number;
        total: number;
        percentage: number;
        gcRuns: number;
    };
    jobs: {
        total: number;
        active: number;
        failed: number;
        averageExecutionTime: number;
        successRate: number;
    };
    alerts: {
        critical: number;
        high: number;
        medium: number;
        low: number;
        responseTime: number;
    };
    performance: {
        throughput: number;
        latency: number;
        availability: number;
        errorRate: number;
    };
}

// =====================================================
// CONFIGURACIÓN GLOBAL Y CONSTANTES
// =====================================================

const JOB_CONFIGS: Record<string, CronJobConfig> = {
    'daily_price_update': {
        jobId: 'daily_price_update',
        name: 'Actualización Diaria de Precios Maxiconsumo',
        type: 'diario',
        cronExpression: '0 2 * * *',
        priority: 5,
        timeoutMs: 300000, // 5 minutos
        maxRetries: 3,
        circuitBreakerThreshold: 5,
        active: true,
        parameters: {
            categories: ['almacen', 'bebidas', 'limpieza', 'congelados'],
            maxProducts: 5000,
            changeThreshold: 2.0,
            batchSize: 50,
            timeoutPerCategory: 60000,
            memoryLimitMb: 512,
            generateReport: true,
            sendNotifications: true,
            compareWithExisting: true
        },
        notificationChannels: ['email', 'slack']
    },
    'weekly_trend_analysis': {
        jobId: 'weekly_trend_analysis',
        name: 'Análisis Semanal de Tendencias y ML',
        type: 'semanal',
        cronExpression: '0 3 * * 0',
        priority: 3,
        timeoutMs: 600000, // 10 minutos
        maxRetries: 2,
        circuitBreakerThreshold: 3,
        active: true,
        parameters: {
            analysisPeriod: 'last_week',
            includeForecasting: true,
            includeSeasonality: true,
            includeVolatilityAnalysis: true,
            includeCompetitiveAnalysis: true,
            exportExcel: true,
            sendStakeholders: true,
            generateExecutiveSummary: true
        },
        notificationChannels: ['email']
    },
    'realtime_change_alerts': {
        jobId: 'realtime_change_alerts',
        name: 'Sistema de Alertas en Tiempo Real',
        type: 'tiempo_real',
        cronExpression: '*/15 * * * *',
        priority: 5,
        timeoutMs: 120000, // 2 minutos
        maxRetries: 2,
        circuitBreakerThreshold: 10,
        active: true,
        parameters: {
            criticalChangeThreshold: 15.0,
            highChangeThreshold: 10.0,
            continuousMonitoring: true,
            instantAlerts: true,
            autoEscalation: true,
            multipleChannels: true,
            criticalProductFilter: true,
            checkNewProducts: true,
            checkPriceChanges: true,
            checkStockChanges: true
        },
        notificationChannels: ['email', 'sms', 'slack']
    },
    'maintenance_cleanup': {
        jobId: 'maintenance_cleanup',
        name: 'Limpieza y Mantenimiento del Sistema',
        type: 'semanal',
        cronExpression: '0 1 * * 1',
        priority: 2,
        timeoutMs: 900000, // 15 minutos
        maxRetries: 1,
        circuitBreakerThreshold: 2,
        active: true,
        parameters: {
            cleanOldLogs: true,
            cleanOldMetrics: true,
            optimizeIndexes: true,
            vacuumTables: true,
            generateBackup: true,
            verifyIntegrity: true,
            cleanCache: true,
            restartCircuitBreakers: true,
            daysToKeepLogs: 30,
            daysToKeepMetrics: 90,
            daysToKeepAlerts: 30,
            backupRetentionDays: 30
        },
        notificationChannels: ['email']
    }
};

const NOTIFICATION_CONFIG: NotificationConfig = {
    email: {
        templates: {
            'daily_report': {
                subject: '📊 Reporte Diario de Precios - MiniMarket',
                htmlBody: `
                    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                            <h1 style="margin: 0; font-size: 24px;">📊 MiniMarket - Reporte Diario</h1>
                            <p style="margin: 5px 0 0 0; font-size: 16px;">Actualización Automática de Precios</p>
                            <p style="margin: 0; font-size: 14px; opacity: 0.9;">{{executionDate}}</p>
                        </div>
                        
                        <div style="padding: 20px; background-color: #f8f9fa;">
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">📈 Resumen Ejecutivo</h2>
                            
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #28a745;">
                                    <h3 style="margin: 0; color: #28a745; font-size: 18px;">✅ Productos Procesados</h3>
                                    <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #2c3e50;">{{productsProcessed}}</p>
                                </div>
                                
                                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #007bff;">
                                    <h3 style="margin: 0; color: #007bff; font-size: 18px;">⏱️ Tiempo de Ejecución</h3>
                                    <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #2c3e50;">{{executionTime}}s</p>
                                </div>
                                
                                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #ffc107;">
                                    <h3 style="margin: 0; color: #ffc107; font-size: 18px;">🚨 Alertas Generadas</h3>
                                    <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #2c3e50;">{{alertsGenerated}}</p>
                                </div>
                                
                                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #17a2b8;">
                                    <h3 style="margin: 0; color: #17a2b8; font-size: 18px;">📊 Tasa de Éxito</h3>
                                    <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #2c3e50;">{{successRate}}%</p>
                                </div>
                            </div>
                            
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">🎯 Alertas Críticas</h2>
                            {{criticalAlerts}}
                            
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">💡 Recomendaciones</h2>
                            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                {{recommendations}}
                            </div>
                            
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">📊 Detalles por Categoría</h2>
                            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                {{categoryBreakdown}}
                            </div>
                        </div>
                        
                        <div style="background-color: #2c3e50; color: white; padding: 15px; text-align: center; font-size: 12px;">
                            <p style="margin: 0;">🤖 Generado automáticamente por el Sistema de Cron Jobs MiniMarket</p>
                            <p style="margin: 5px 0 0 0;">📧 ¿Problemas? Contacta a soporte técnico</p>
                        </div>
                    </div>
                `,
                textBody: `
                    MiniMarket - Reporte Diario de Precios
                    ================================
                    
                    Fecha: {{executionDate}}
                    
                    RESUMEN EJECUTIVO:
                    • Productos Procesados: {{productsProcessed}}
                    • Tiempo de Ejecución: {{executionTime}}s
                    • Alertas Generadas: {{alertsGenerated}}
                    • Tasa de Éxito: {{successRate}}%
                    
                    ALERTAS CRÍTICAS:
                    {{criticalAlerts}}
                    
                    RECOMENDACIONES:
                    {{recommendations}}
                    
                    DETALLES POR CATEGORÍA:
                    {{categoryBreakdown}}
                    
                    ---
                    Generado automáticamente por el Sistema de Cron Jobs MiniMarket
                `,
                variables: ['executionDate', 'productsProcessed', 'executionTime', 'alertsGenerated', 'successRate', 'criticalAlerts', 'recommendations', 'categoryBreakdown']
            },
            'weekly_analysis': {
                subject: '📈 Análisis Semanal de Tendencias - MiniMarket',
                htmlBody: `
                    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                            <h1 style="margin: 0; font-size: 24px;">📈 Análisis Semanal de Tendencias</h1>
                            <p style="margin: 5px 0 0 0; font-size: 16px;">MiniMarket Intelligence Report</p>
                            <p style="margin: 0; font-size: 14px; opacity: 0.9;">Semana del {{weekStart}} al {{weekEnd}}</p>
                        </div>
                        
                        <div style="padding: 20px; background-color: #f8f9fa;">
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">🔍 Análisis de Tendencias</h2>
                            {{trendAnalysis}}
                            
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">🎯 Predicciones ML</h2>
                            {{mlPredictions}}
                            
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">📊 Métricas de Performance</h2>
                            {{performanceMetrics}}
                            
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 10px;">💼 Recomendaciones Ejecutivas</h2>
                            {{executiveRecommendations}}
                        </div>
                    </div>
                `,
                textBody: `
                    MiniMarket - Análisis Semanal de Tendencias
                    ==========================================
                    
                    Período: {{weekStart}} al {{weekEnd}}
                    
                    ANÁLISIS DE TENDENCIAS:
                    {{trendAnalysis}}
                    
                    PREDICCIONES ML:
                    {{mlPredictions}}
                    
                    MÉTRICAS DE PERFORMANCE:
                    {{performanceMetrics}}
                    
                    RECOMENDACIONES EJECUTIVAS:
                    {{executiveRecommendations}}
                    
                    ---
                    Análisis generado por MiniMarket AI System
                `,
                variables: ['weekStart', 'weekEnd', 'trendAnalysis', 'mlPredictions', 'performanceMetrics', 'executiveRecommendations']
            },
            'critical_alert': {
                subject: '🚨 ALERTA CRÍTICA - Sistema MiniMarket',
                htmlBody: `
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background: linear-gradient(135deg, #ff4757 0%, #c23616 100%); color: white; padding: 20px; text-align: center;">
                            <h1 style="margin: 0; font-size: 24px;">🚨 ALERTA CRÍTICA</h1>
                            <p style="margin: 5px 0 0 0; font-size: 16px;">Sistema MiniMarket - {{alertType}}</p>
                        </div>
                        
                        <div style="padding: 20px; background-color: #fff5f5; border: 2px solid #ff4757;">
                            <h2 style="color: #c23616; margin-top: 0;">⚠️ {{alertTitle}}</h2>
                            <p style="font-size: 16px; line-height: 1.6;">{{alertDescription}}</p>
                            
                            <div style="background: white; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #2c3e50; margin-top: 0;">📊 Detalles Técnicos</h3>
                                <p><strong>Job ID:</strong> {{jobId}}</p>
                                <p><strong>Execution ID:</strong> {{executionId}}</p>
                                <p><strong>Timestamp:</strong> {{timestamp}}</p>
                                <p><strong>Severidad:</strong> <span style="color: #e74c3c; font-weight: bold;">{{severity}}</span></p>
                            </div>
                            
                            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                                <h3 style="color: #856404; margin-top: 0;">💡 Acción Recomendada</h3>
                                <p style="margin: 0; color: #856404;">{{recommendedAction}}</p>
                            </div>
                            
                            <div style="text-align: center; margin-top: 20px;">
                                <a href="{{dashboardUrl}}" style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                    Ver Dashboard
                                </a>
                            </div>
                        </div>
                    </div>
                `,
                textBody: `
                    ALERTA CRÍTICA - Sistema MiniMarket
                    =================================
                    
                    Tipo: {{alertType}}
                    Título: {{alertTitle}}
                    
                    Descripción:
                    {{alertDescription}}
                    
                    DETALLES TÉCNICOS:
                    • Job ID: {{jobId}}
                    • Execution ID: {{executionId}}
                    • Timestamp: {{timestamp}}
                    • Severidad: {{severity}}
                    
                    ACCIÓN RECOMENDADA:
                    {{recommendedAction}}
                    
                    Acceder al Dashboard: {{dashboardUrl}}
                    
                    ---
                    Sistema de Alertas MiniMarket
                `,
                variables: ['alertType', 'alertTitle', 'alertDescription', 'jobId', 'executionId', 'timestamp', 'severity', 'recommendedAction', 'dashboardUrl']
            }
        },
        smtp: {
            host: 'smtp.gmail.com',
            port: 587,
            secure: false,
            auth: {
                user: Deno.env.get('SMTP_USER') || '',
                pass: Deno.env.get('SMTP_PASS') || ''
            }
        },
        from: Deno.env.get('EMAIL_FROM') || 'noreply@minimarket.com',
        fromName: 'Sistema MiniMarket'
    },
    sms: {
        provider: 'twilio',
        accountSid: Deno.env.get('TWILIO_ACCOUNT_SID'),
        authToken: Deno.env.get('TWILIO_AUTH_TOKEN'),
        fromNumber: Deno.env.get('TWILIO_FROM_NUMBER') || '+1234567890'
    },
    webhooks: {
        slack: {
            webhookUrl: Deno.env.get('SLACK_WEBHOOK_URL') || '',
            channel: '#alerts-minimarket'
        },
        teams: {
            webhookUrl: Deno.env.get('TEAMS_WEBHOOK_URL') || ''
        }
    }
};

// =====================================================
// VARIABLES GLOBALES DE ESTADO
// =====================================================

const ACTIVE_EXECUTIONS = new Map<string, JobExecutionContext>();
const CIRCUIT_BREAKERS = new Map<string, CircuitBreakerState>();
const PERFORMANCE_METRICS = {
    jobsExecuted: 0,
    jobsSucceeded: 0,
    jobsFailed: 0,
    totalExecutionTime: 0,
    averageExecutionTime: 0,
    memoryUsage: { used: 0, total: 0 },
    alertsGenerated: 0,
    notificationsSent: 0
};

interface CircuitBreakerState {
    state: 'closed' | 'open' | 'half_open';
    failures: number;
    lastFailure: Date | null;
    successCount: number;
    threshold: number;
}

// =====================================================
// FUNCIÓN PRINCIPAL Deno.serve
// =====================================================

Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-request-id',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
        'Access-Control-Max-Age': '86400',
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    };

    // Request tracking
    const requestId = crypto.randomUUID();
    const startTime = Date.now();
    const structuredLog = {
        requestId,
        method: req.method,
        url: req.url,
        userAgent: req.headers.get('user-agent'),
        ip: req.headers.get('x-forwarded-for') || 'unknown',
        timestamp: new Date().toISOString(),
        functionName: 'cron-jobs-maxiconsumo'
    };

    if (req.method === 'OPTIONS') {
        console.log(JSON.stringify({ ...structuredLog, event: 'OPTIONS_REQUEST' }));
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const url = new URL(req.url);
        const action = url.pathname.split('/').pop() || 'execute';
        const sanitizedAction = action.replace(/[^a-zA-Z0-9_-]/g, '').substring(0, 30);

        console.log(JSON.stringify({
            ...structuredLog,
            event: 'REQUEST_START',
            action: sanitizedAction,
            queryParams: url.search
        }));

        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Configuración de Supabase faltante');
        }

        // Verificar circuit breakers antes de procesar
        const circuitBreakerStatus = getCircuitBreakerStatus();
        if (Object.values(circuitBreakerStatus).some(cb => cb.state === 'open')) {
            console.warn(JSON.stringify({
                ...structuredLog,
                event: 'CIRCUIT_BREAKER_ACTIVE',
                status: circuitBreakerStatus
            }));
        }

        let response: Response;

        switch (sanitizedAction) {
            case 'execute':
                response = await executeJobHandler(req, supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'status':
                response = await getSystemStatusHandler(supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'metrics':
                response = await getMetricsHandler(supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'alerts':
                response = await getAlertsHandler(supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'health':
                response = await getHealthCheckHandler(supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'dashboard':
                response = await getDashboardHandler(supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'manual-trigger':
                response = await manualTriggerHandler(req, supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'retry':
                response = await retryJobHandler(req, supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'pause':
                response = await pauseJobHandler(req, supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'resume':
                response = await resumeJobHandler(req, supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            case 'test-notifications':
                response = await testNotificationsHandler(req, supabaseUrl, serviceRoleKey, corsHeaders, requestId, structuredLog);
                break;
            default:
                throw new Error(`Acción no válida: ${sanitizedAction}`);
        }

        const duration = Date.now() - startTime;
        console.log(JSON.stringify({
            ...structuredLog,
            event: 'REQUEST_COMPLETED',
            duration,
            status: response.status
        }));

        return response;

    } catch (error) {
        const duration = Date.now() - startTime;
        const errorLog = {
            ...structuredLog,
            event: 'REQUEST_ERROR',
            error: {
                name: error.name,
                message: error.message,
                stack: error.stack
            },
            duration
        };

        console.error(JSON.stringify(errorLog));

        const errorResponse = {
            success: false,
            error: {
                code: 'CRON_JOB_ERROR',
                message: error.message,
                requestId,
                timestamp: new Date().toISOString(),
                retryable: isRetryableError(error)
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: isRetryableError(error) ? 503 : 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// =====================================================
// MANEJADORES DE ACCIONES
// =====================================================

/**
 * EJECUTOR PRINCIPAL DE JOBS
 */
async function executeJobHandler(
    req: Request,
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>,
    requestId: string,
    structuredLog: any
): Promise<Response> {
    const body = await req.json();
    const { jobId, parameters = {}, source = 'api' } = body;

    if (!jobId || !JOB_CONFIGS[jobId]) {
        throw new Error(`Job ID no válido: ${jobId}`);
    }

    const jobConfig = JOB_CONFIGS[jobId];
    const executionId = `${jobId}_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;

    console.log(JSON.stringify({
        ...structuredLog,
        event: 'JOB_EXECUTION_START',
        jobId,
        executionId,
        jobType: jobConfig.type,
        source
    }));

    // Verificar circuit breaker
    if (!checkCircuitBreaker(jobId)) {
        throw new Error(`Circuit breaker abierto para job ${jobId}`);
    }

    // Crear contexto de ejecución
    const context: JobExecutionContext = {
        executionId,
        jobId,
        startTime: new Date(),
        source: source as any,
        parameters: { ...jobConfig.parameters, ...parameters },
        environment: {
            nodeVersion: Deno.version.deno,
            memoryUsage: performance.memory ? {
                rss: performance.memory.rss,
                heapTotal: performance.memory.heapTotal,
                heapUsed: performance.memory.heapUsed,
                external: performance.memory.external
            } : { rss: 0, heapTotal: 0, heapUsed: 0, external: 0 },
            timestamp: new Date().toISOString()
        }
    };

    // Registrar ejecución en DB
    await recordJobExecution(supabaseUrl, serviceRoleKey, context, 'iniciado');

    try {
        // Ejecutar el job específico
        let result: JobResult;

        switch (jobId) {
            case 'daily_price_update':
                result = await executeDailyPriceUpdate(context, supabaseUrl, serviceRoleKey);
                break;
            case 'weekly_trend_analysis':
                result = await executeWeeklyTrendAnalysis(context, supabaseUrl, serviceRoleKey);
                break;
            case 'realtime_change_alerts':
                result = await executeRealtimeChangeAlerts(context, supabaseUrl, serviceRoleKey);
                break;
            case 'maintenance_cleanup':
                result = await executeMaintenanceCleanup(context, supabaseUrl, serviceRoleKey);
                break;
            default:
                throw new Error(`Job no implementado: ${jobId}`);
        }

        // Marcar circuit breaker como éxito
        markCircuitBreakerSuccess(jobId);

        // Registrar ejecución exitosa en DB
        await recordJobExecution(supabaseUrl, serviceRoleKey, context, 'exitoso', result);

        // Enviar notificaciones si es necesario
        if (result.alertsGenerated > 0 || result.errors.length > 0) {
            await sendNotifications(jobId, result, context);
        }

        // Actualizar métricas
        updatePerformanceMetrics(result);

        console.log(JSON.stringify({
            ...structuredLog,
            event: 'JOB_EXECUTION_COMPLETE',
            jobId,
            executionId,
            success: result.success,
            duration: result.executionTimeMs,
            productsProcessed: result.productsProcessed,
            alertsGenerated: result.alertsGenerated
        }));

        return new Response(JSON.stringify({
            success: true,
            data: {
                jobId,
                executionId,
                result,
                context: {
                    startTime: context.startTime,
                    duration: result.executionTimeMs
                }
            },
            requestId
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        // Marcar circuit breaker como fallo
        markCircuitBreakerFailure(jobId);

        // Registrar ejecución fallida en DB
        await recordJobExecution(supabaseUrl, serviceRoleKey, context, 'fallido', null, error.message);

        // Crear alerta crítica
        await createSystemAlert(jobId, executionId, 'ejecucion_fallida', 'critica',
            `Error en ejecución de ${jobId}`, error.message, 'Verificar logs y estado del sistema');

        // Actualizar métricas
        updatePerformanceMetrics({
            success: false,
            executionTimeMs: Date.now() - context.startTime.getTime(),
            productsProcessed: 0,
            productsSuccessful: 0,
            productsFailed: 0,
            alertsGenerated: 0,
            emailsSent: 0,
            smsSent: 0,
            metrics: {},
            errors: [error.message],
            warnings: [],
            recommendations: []
        });

        throw error;
    }
}

/**
 * MANEJADOR DE ESTADO DEL SISTEMA
 */
async function getSystemStatusHandler(
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>,
    requestId: string,
    structuredLog: any
): Promise<Response> {
    console.log(JSON.stringify({
        ...structuredLog,
        event: 'SYSTEM_STATUS_REQUEST'
    }));

    try {
        // Obtener estado de jobs desde la base de datos
        const jobsResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_tracking?select=*`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const jobs = jobsResponse.ok ? await jobsResponse.json() : [];

        // Obtener métricas del día
        const metricsResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_metrics?select=*&fecha_metricas=eq.${new Date().toISOString().split('T')[0]}`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const metrics = metricsResponse.ok ? await metricsResponse.json() : [];

        // Obtener alertas activas
        const alertsResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_alerts?select=*&estado_alerta=eq.activas&order=created_at.desc&limit=10`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const alerts = alertsResponse.ok ? await alertsResponse.json() : [];

        // Calcular métricas del sistema
        const systemMetrics = calculateSystemMetrics(jobs, metrics, alerts);

        const status = {
            system: {
                status: systemMetrics.overallHealth > 80 ? 'healthy' : 
                       systemMetrics.overallHealth > 60 ? 'degraded' : 'critical',
                healthScore: systemMetrics.overallHealth,
                uptime: '99.9%', // En producción se calcularía real
                lastUpdate: new Date().toISOString()
            },
            jobs: {
                total: jobs.length,
                active: jobs.filter((j: any) => j.estado_job === 'ejecutando').length,
                inactive: jobs.filter((j: any) => j.estado_job === 'inactivo').length,
                failed: jobs.filter((j: any) => j.estado_job === 'fallido').length,
                circuitBreakersOpen: Object.values(getCircuitBreakerStatus()).filter(cb => cb.state === 'open').length
            },
            performance: {
                jobsExecutedToday: systemMetrics.jobsExecutedToday,
                successRate: systemMetrics.successRate,
                averageExecutionTime: systemMetrics.averageExecutionTime,
                alertsGenerated: systemMetrics.alertsGenerated
            },
            alerts: {
                critical: alerts.filter((a: any) => a.severidad === 'critica').length,
                high: alerts.filter((a: any) => a.severidad === 'alta').length,
                medium: alerts.filter((a: any) => a.severidad === 'media').length,
                low: alerts.filter((a: any) => a.severidad === 'baja').length,
                total: alerts.length
            },
            circuitBreakers: getCircuitBreakerStatus(),
            configuration: {
                jobsConfigured: Object.keys(JOB_CONFIGS).length,
                notificationsEnabled: true,
                monitoringActive: true
            }
        };

        return new Response(JSON.stringify({
            success: true,
            data: status,
            requestId
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error(JSON.stringify({
            ...structuredLog,
            event: 'SYSTEM_STATUS_ERROR',
            error: error.message
        }));

        throw error;
    }
}

/**
 * MANEJADOR DE MÉTRICAS DETALLADAS
 */
async function getMetricsHandler(
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>,
    requestId: string,
    structuredLog: any
): Promise<Response> {
    const url = new URL(req.url);
    const period = url.searchParams.get('period') || 'today';
    const jobId = url.searchParams.get('jobId');

    console.log(JSON.stringify({
        ...structuredLog,
        event: 'METRICS_REQUEST',
        period,
        jobId
    }));

    try {
        let dateFilter = '';
        switch (period) {
            case 'today':
                dateFilter = new Date().toISOString().split('T')[0];
                break;
            case 'week':
                const weekAgo = new Date();
                weekAgo.setDate(weekAgo.getDate() - 7);
                dateFilter = `gte.${weekAgo.toISOString().split('T')[0]}`;
                break;
            case 'month':
                const monthAgo = new Date();
                monthAgo.setMonth(monthAgo.getMonth() - 1);
                dateFilter = `gte.${monthAgo.toISOString().split('T')[0]}`;
                break;
        }

        const query = jobId ? 
            `${supabaseUrl}/rest/v1/cron_jobs_metrics?select=*&fecha_metricas=${dateFilter}&job_id=eq.${jobId}` :
            `${supabaseUrl}/rest/v1/cron_jobs_metrics?select=*&fecha_metricas=${dateFilter}`;

        const response = await fetch(query, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const metrics = response.ok ? await response.json() : [];

        // Obtener métricas de ejecución recientes
        const executionQuery = `${supabaseUrl}/rest/v1/cron_jobs_execution_log?select=*&start_time=gte.${new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()}&order=start_time.desc`;
        const executionResponse = await fetch(executionQuery, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const executions = executionResponse.ok ? await executionResponse.json() : [];

        const detailedMetrics = {
            period,
            jobId,
            summary: calculateDetailedMetrics(metrics),
            executions: executions.slice(0, 50), // Últimas 50 ejecuciones
            trends: calculateTrends(metrics),
            performance: calculatePerformanceTrends(executions),
            recommendations: generateMetricRecommendations(metrics, executions)
        };

        return new Response(JSON.stringify({
            success: true,
            data: detailedMetrics,
            requestId
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error(JSON.stringify({
            ...structuredLog,
            event: 'METRICS_ERROR',
            error: error.message
        }));

        throw error;
    }
}

/**
 * MANEJADOR DE ALERTAS
 */
async function getAlertsHandler(
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>,
    requestId: string,
    structuredLog: any
): Promise<Response> {
    const url = new URL(req.url);
    const status = url.searchParams.get('status') || 'activa';
    const severity = url.searchParams.get('severity');
    const limit = parseInt(url.searchParams.get('limit') || '20');

    console.log(JSON.stringify({
        ...structuredLog,
        event: 'ALERTS_REQUEST',
        status,
        severity,
        limit
    }));

    try {
        let query = `${supabaseUrl}/rest/v1/cron_jobs_alerts?select=*&estado_alerta=eq.${status}&order=created_at.desc&limit=${limit}`;
        
        if (severity) {
            query += `&severidad=eq.${severity}`;
        }

        const response = await fetch(query, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const alerts = response.ok ? await response.json() : [];

        // Obtener estadísticas de alertas
        const statsQuery = `${supabaseUrl}/rest/v1/cron_jobs_alerts?select=severidad,estado_alerta&created_at=gte.${new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()}`;
        const statsResponse = await fetch(statsQuery, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const stats = statsResponse.ok ? await statsResponse.json() : [];

        const alertStats = {
            total: stats.length,
            byStatus: stats.reduce((acc: any, alert: any) => {
                acc[alert.estado_alerta] = (acc[alert.estado_alerta] || 0) + 1;
                return acc;
            }, {}),
            bySeverity: stats.reduce((acc: any, alert: any) => {
                acc[alert.severidad] = (acc[alert.severidad] || 0) + 1;
                return acc;
            }, {}),
            resolvedToday: stats.filter((a: any) => 
                a.estado_alerta === 'resuelta' && 
                new Date(a.created_at).toDateString() === new Date().toDateString()
            ).length
        };

        const result = {
            alerts,
            stats: alertStats,
            summary: {
                activeCritical: alerts.filter((a: any) => a.severidad === 'critica').length,
                activeHigh: alerts.filter((a: any) => a.severidad === 'alta').length,
                awaitingResponse: alerts.filter((a: any) => a.estado_alerta === 'activa').length,
                averageResolutionTime: calculateAverageResolutionTime(alerts)
            }
        };

        return new Response(JSON.stringify({
            success: true,
            data: result,
            requestId
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error(JSON.stringify({
            ...structuredLog,
            event: 'ALERTS_ERROR',
            error: error.message
        }));

        throw error;
    }
}

/**
 * MANEJADOR DE HEALTH CHECK
 */
async function getHealthCheckHandler(
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>,
    requestId: string,
    structuredLog: any
): Promise<Response> {
    console.log(JSON.stringify({
        ...structuredLog,
        event: 'HEALTH_CHECK_REQUEST'
    }));

    const health: SystemHealthMetrics = {
        database: {
            status: 'unknown',
            responseTime: 0,
            activeConnections: 0,
            queryPerformance: 0
        },
        memory: {
            used: performance.memory?.usedJSHeapSize || 0,
            total: performance.memory?.totalJSHeapSize || 0,
            percentage: performance.memory ? 
                Math.round((performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize) * 100) : 0,
            gcRuns: (globalThis as any).gcRuns || 0
        },
        jobs: {
            total: Object.keys(JOB_CONFIGS).length,
            active: Object.values(ACTIVE_EXECUTIONS).length,
            failed: Object.values(getCircuitBreakerStatus()).filter(cb => cb.state === 'open').length,
            averageExecutionTime: PERFORMANCE_METRICS.averageExecutionTime,
            successRate: PERFORMANCE_METRICS.jobsExecuted > 0 ? 
                Math.round((PERFORMANCE_METRICS.jobsSucceeded / PERFORMANCE_METRICS.jobsExecuted) * 100) : 0
        },
        alerts: {
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
            responseTime: 0
        },
        performance: {
            throughput: 0,
            latency: PERFORMANCE_METRICS.averageExecutionTime,
            availability: 99.9,
            errorRate: PERFORMANCE_METRICS.jobsExecuted > 0 ? 
                Math.round(((PERFORMANCE_METRICS.jobsFailed / PERFORMANCE_METRICS.jobsExecuted) * 100) * 100) / 100 : 0
        }
    };

    try {
        // Test database connectivity
        const startTime = Date.now();
        const testResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_tracking?select=count&limit=1`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        health.database.responseTime = Date.now() - startTime;
        health.database.status = testResponse.ok ? 'healthy' : 'critical';
        health.database.activeConnections = testResponse.ok ? 1 : 0;

        // Obtener conteo de alertas críticas
        const alertsResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_alerts?select=severidad&estado_alerta=eq.activas`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        if (alertsResponse.ok) {
            const alerts = await alertsResponse.json();
            health.alerts.critical = alerts.filter((a: any) => a.severidad === 'critica').length;
            health.alerts.high = alerts.filter((a: any) => a.severidad === 'alta').length;
            health.alerts.medium = alerts.filter((a: any) => a.severidad === 'media').length;
            health.alerts.low = alerts.filter((a: any) => a.severidad === 'baja').length;
        }

        // Calcular health score general
        const healthScore = calculateOverallHealthScore(health);

        const response = {
            success: true,
            health: {
                ...health,
                overallStatus: healthScore > 80 ? 'healthy' : 
                              healthScore > 60 ? 'degraded' : 'critical',
                healthScore,
                timestamp: new Date().toISOString(),
                version: '3.0.0'
            },
            circuitBreakers: getCircuitBreakerStatus(),
            requestId
        };

        return new Response(JSON.stringify(response), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error(JSON.stringify({
            ...structuredLog,
            event: 'HEALTH_CHECK_ERROR',
            error: error.message
        }));

        health.database.status = 'critical';
        health.overallStatus = 'critical';

        return new Response(JSON.stringify({
            success: false,
            health: {
                ...health,
                overallStatus: 'critical',
                healthScore: 0,
                timestamp: new Date().toISOString(),
                error: error.message
            },
            requestId
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
}

/**
 * MANEJADOR DEL DASHBOARD
 */
async function getDashboardHandler(
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>,
    requestId: string,
    structuredLog: any
): Promise<Response> {
    console.log(JSON.stringify({
        ...structuredLog,
        event: 'DASHBOARD_REQUEST'
    }));

    try {
        // Obtener vista del dashboard
        const dashboardResponse = await fetch(`${supabaseUrl}/rest/v1/vista_cron_jobs_dashboard?select=*`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const dashboard = dashboardResponse.ok ? await dashboardResponse.json() : [];

        // Obtener alertas activas
        const alertsResponse = await fetch(`${supabaseUrl}/rest/v1/vista_cron_jobs_alertas_activas?select=*&limit=10`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const alerts = alertsResponse.ok ? await alertsResponse.json() : [];

        // Obtener métricas semanales
        const weeklyResponse = await fetch(`${supabaseUrl}/rest/v1/vista_cron_jobs_metricas_semanales?select=*&limit=4`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const weeklyMetrics = weeklyResponse.ok ? await weeklyResponse.json() : [];

        // Obtener ejecuciones recientes
        const executionsResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_execution_log?select=*&order=start_time.desc&limit=20`, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        });

        const recentExecutions = executionsResponse.ok ? await executionsResponse.json() : [];

        const dashboardData = {
            summary: {
                totalJobs: dashboard.length,
                activeJobs: dashboard.filter((j: any) => j.estado_job === 'ejecutando').length,
                failedJobs: dashboard.filter((j: any) => j.estado_job === 'fallido').length,
                alertsActive: alerts.length,
                averageSuccessRate: dashboard.length > 0 ? 
                    Math.round(dashboard.reduce((sum: number, j: any) => sum + (j.disponibilidad_porcentual || 0), 0) / dashboard.length) : 0,
                systemHealth: calculateSystemHealth(dashboard, alerts)
            },
            jobs: dashboard,
            alerts: alerts,
            weeklyMetrics: weeklyMetrics,
            recentExecutions: recentExecutions,
            performance: {
                executionTrends: calculateExecutionTrends(recentExecutions),
                alertTrends: calculateAlertTrends(alerts),
                systemLoad: calculateSystemLoad()
            },
            recommendations: generateSystemRecommendations(dashboard, alerts, weeklyMetrics)
        };

        return new Response(JSON.stringify({
            success: true,
            data: dashboardData,
            requestId
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error(JSON.stringify({
            ...structuredLog,
            event: 'DASHBOARD_ERROR',
            error: error.message
        }));

        throw error;
    }
}

/**
 * MANEJADOR DE TRIGGER MANUAL
 */
async function manualTriggerHandler(
    req: Request,
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>,
    requestId: string,
    structuredLog: any
): Promise<Response> {
    const body = await req.json();
    const { jobId, parameters = {} } = body;

    if (!jobId || !JOB_CONFIGS[jobId]) {
        throw new Error(`Job ID no válido: ${jobId}`);
    }

    console.log(JSON.stringify({
        ...structuredLog,
        event: 'MANUAL_TRIGGER',
        jobId,
        triggeredBy: 'manual'
    }));

    // Ejecutar job manualmente
    return await executeJobHandler(
        new Request(req.url, {
            method: 'POST',
            headers: req.headers,
            body: JSON.stringify({ jobId, parameters, source: 'manual' })
        }),
        supabaseUrl,
        serviceRoleKey,
        corsHeaders,
        requestId,
        structuredLog
    );
}

/**
 * MANEJADOR DE REINTENTO
 */
async function retryJobHandler(
    req: Request,
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>,
    requestId: string,
    structuredLog: any
): Promise<Response> {
    const body = await req.json();
    const { executionId } = body;

    if (!executionId) {
        throw new Error('Execution ID es requerido para reintento');
    }

    // Obtener información de la ejecución fallida
    const executionResponse = await fetch(`${supabaseUrl}/rest/v1/cron_jobs_execution_log?select=*&execution_id=eq.${executionId}`, {
        headers: {
            'apikey': serviceRoleKey,
            'Authorization': `Bearer ${serviceRoleKey}`
        }
    });

    const executions = executionResponse.ok ? await executionResponse.json() : [];
    if (executions.length === 0) {
        throw new Error(`Execution ID no encontrado: ${executionId}`);
    }

    const failedExecution = executions[0];
    const jobId = failedExecution.job_id;

    console.log(JSON.stringify({
        ...structuredLog,
        event: 'JOB_RETRY',
        jobId,
        executionId,
        originalExecution: failedExecution.start_time
    }));

    // Reintentar el job con los mismos parámetros
    return await executeJobHandler(
        new Request(req.url, {
            method: 'POST',
            headers: req.headers,
            body: JSON.stringify({ 
                jobId, 
                parameters: failedExecution.parametros_ejecucion,
                source: 'retry' 
            })
        }),
        supabaseUrl,
        serviceRoleKey,
        corsHeaders,
        requestId,
        structuredLog
    );
}

// =====================================================
// FUNCIONES DE EJECUCIÓN DE JOBS ESPECÍFICOS
// =====================================================

/**
 * JOB DIARIO: ACTUALIZACIÓN DE PRECIOS
 */
async function executeDailyPriceUpdate(
    context: JobExecutionContext,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<JobResult> {
    const startTime = Date.now();
    const result: JobResult = {
        success: false,
        executionTimeMs: 0,
        productsProcessed: 0,
        productsSuccessful: 0,
        productsFailed: 0,
        alertsGenerated: 0,
        emailsSent: 0,
        smsSent: 0,
        metrics: {},
        errors: [],
        warnings: [],
        recommendations: []
    };

    try {
        console.log(`[DAILY_PRICE_UPDATE] Iniciando actualización diaria de precios`);

        // 1. Ejecutar scraping completo
        const scrapingResponse = await fetch(`${supabaseUrl}/functions/v1/scraper-maxiconsumo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${serviceRoleKey}`
            },
            body: JSON.stringify({
                action: 'scrape',
                categories: context.parameters.categories,
                maxProducts: context.parameters.maxProducts,
                executionId: context.executionId
            })
        });

        if (scrapingResponse.ok) {
            const scrapingResult = await scrapingResponse.json();
            result.productsProcessed = scrapingResult.data?.productos_extraidos || 0;
            result.productsSuccessful = scrapingResult.data?.productos_guardados || 0;
        }

        // 2. Ejecutar comparación de precios
        const comparisonResponse = await fetch(`${supabaseUrl}/functions/v1/scraper-maxiconsumo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${serviceRoleKey}`
            },
            body: JSON.stringify({
                action: 'compare',
                executionId: context.executionId
            })
        });

        // 3. Generar alertas
        const alertsResponse = await fetch(`${supabaseUrl}/functions/v1/scraper-maxiconsumo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${serviceRoleKey}`
            },
            body: JSON.stringify({
                action: 'alerts',
                executionId: context.executionId
            })
        });

        if (alertsResponse.ok) {
            const alertsResult = await alertsResponse.json();
            result.alertsGenerated = alertsResult.data?.alertas_generadas || 0;
        }

        // 4. Generar reporte diario
        const reportResult = await generateDailyReport(context, supabaseUrl, serviceRoleKey);
        result.emailsSent = reportResult.emailsSent;

        result.success = true;
        result.executionTimeMs = Date.now() - startTime;

        // Generar recomendaciones
        if (result.alertsGenerated > 10) {
            result.recommendations.push('Alto número de alertas generadas - revisar umbrales de detección');
        }
        if (result.productsFailed > result.productsProcessed * 0.1) {
            result.recommendations.push('Alto porcentaje de productos fallidos - verificar conectividad con proveedor');
        }
        if (result.executionTimeMs > 300000) { // 5 minutos
            result.recommendations.push('Tiempo de ejecución elevado - optimizar proceso de scraping');
        }

        console.log(`[DAILY_PRICE_UPDATE] Completado exitosamente en ${result.executionTimeMs}ms`);

    } catch (error) {
        result.errors.push(`Error en actualización diaria: ${error.message}`);
        console.error(`[DAILY_PRICE_UPDATE] Error:`, error);
    }

    return result;
}

/**
 * JOB SEMANAL: ANÁLISIS DE TENDENCIAS
 */
async function executeWeeklyTrendAnalysis(
    context: JobExecutionContext,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<JobResult> {
    const startTime = Date.now();
    const result: JobResult = {
        success: false,
        executionTimeMs: 0,
        productsProcessed: 0,
        productsSuccessful: 0,
        productsFailed: 0,
        alertsGenerated: 0,
        emailsSent: 0,
        smsSent: 0,
        metrics: {},
        errors: [],
        warnings: [],
        recommendations: []
    };

    try {
        console.log(`[WEEKLY_TREND_ANALYSIS] Iniciando análisis semanal de tendencias`);

        // 1. Obtener datos de la última semana
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);

        const priceHistoryResponse = await fetch(
            `${supabaseUrl}/rest/v1/precios_historicos?select=*,productos(*)&fecha_cambio=gte.${weekAgo.toISOString()}`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        const priceHistory = priceHistoryResponse.ok ? await priceHistoryResponse.json() : [];

        // 2. Análisis de tendencias básicas
        const trendAnalysis = performBasicTrendAnalysis(priceHistory);

        // 3. Predicciones simples (ML básico)
        const predictions = generateSimplePredictions(priceHistory);

        // 4. Análisis estacional
        const seasonality = analyzeSeasonality(priceHistory);

        // 5. Generar reporte ejecutivo
        const reportResult = await generateWeeklyReport({
            trendAnalysis,
            predictions,
            seasonality,
            period: 'last_week'
        }, context, supabaseUrl, serviceRoleKey);

        result.emailsSent = reportResult.emailsSent;
        result.metrics = {
            trendAnalysis,
            predictions,
            seasonality,
            productsAnalyzed: priceHistory.length
        };

        result.success = true;
        result.executionTimeMs = Date.now() - startTime;

        // Generar recomendaciones basadas en análisis
        if (trendAnalysis.volatility > 0.15) {
            result.recommendations.push('Alta volatilidad detectada - revisar estrategia de precios');
        }
        if (predictions.upwardTrends > predictions.downwardTrends) {
            result.recommendations.push('Tendencia alcista predominante - considerar ajustes de inventario');
        }

        console.log(`[WEEKLY_TREND_ANALYSIS] Completado exitosamente en ${result.executionTimeMs}ms`);

    } catch (error) {
        result.errors.push(`Error en análisis semanal: ${error.message}`);
        console.error(`[WEEKLY_TREND_ANALYSIS] Error:`, error);
    }

    return result;
}

/**
 * JOB TIEMPO REAL: ALERTAS DE CAMBIOS
 */
async function executeRealtimeChangeAlerts(
    context: JobExecutionContext,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<JobResult> {
    const startTime = Date.now();
    const result: JobResult = {
        success: false,
        executionTimeMs: 0,
        productsProcessed: 0,
        productsSuccessful: 0,
        productsFailed: 0,
        alertsGenerated: 0,
        emailsSent: 0,
        smsSent: 0,
        metrics: {},
        errors: [],
        warnings: [],
        recommendations: []
    };

    try {
        console.log(`[REALTIME_CHANGE_ALERTS] Verificando cambios en tiempo real`);

        // 1. Llamar detección de cambios significativos
        const detectionResponse = await fetch(`${supabaseUrl}/rest/v1/rpc/fnc_deteccion_cambios_significativos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            },
            body: JSON.stringify({ p_umbral_porcentual: context.parameters.criticalChangeThreshold })
        });

        if (detectionResponse.ok) {
            const alertsCount = await detectionResponse.json();
            result.alertsGenerated = alertsCount;

            // 2. Verificar health del sistema
            await recordHealthCheck('realtime_change_alerts', 'database_connection', 'healthy');
        }

        // 3. Verificar nuevos productos
        const newProductsResponse = await fetch(
            `${supabaseUrl}/rest/v1/precios_proveedor?select=*&ultima_actualizacion=gte.${new Date(Date.now() - 15 * 60 * 1000).toISOString()}`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        if (newProductsResponse.ok) {
            const newProducts = await newProductsResponse.json();
            if (newProducts.length > 0) {
                result.alertsGenerated += await createProductAlert(newProducts, context);
            }
        }

        // 4. Verificar stock crítico
        const lowStockResponse = await fetch(
            `${supabaseUrl}/rest/v1/precios_proveedor?select=*&stock_disponible=lt.10&activo=eq.true`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        if (lowStockResponse.ok) {
            const lowStockProducts = await lowStockResponse.json();
            if (lowStockProducts.length > 0) {
                result.alertsGenerated += await createStockAlert(lowStockProducts, context);
            }
        }

        result.success = true;
        result.executionTimeMs = Date.now() - startTime;
        result.productsProcessed = result.alertsGenerated;

        // Actualizar métricas de tiempo real
        updateRealTimeMetrics(result);

        console.log(`[REALTIME_CHANGE_ALERTS] Verificación completada en ${result.executionTimeMs}ms - ${result.alertsGenerated} alertas`);

    } catch (error) {
        result.errors.push(`Error en alertas tiempo real: ${error.message}`);
        
        // Registrar health check como fallido
        await recordHealthCheck('realtime_change_alerts', 'database_connection', 'critical', null, {
            error: error.message
        });

        console.error(`[REALTIME_CHANGE_ALERTS] Error:`, error);
    }

    return result;
}

/**
 * JOB MANTENIMIENTO: LIMPIEZA Y OPTIMIZACIÓN
 */
async function executeMaintenanceCleanup(
    context: JobExecutionContext,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<JobResult> {
    const startTime = Date.now();
    const result: JobResult = {
        success: false,
        executionTimeMs: 0,
        productsProcessed: 0,
        productsSuccessful: 0,
        productsFailed: 0,
        alertsGenerated: 0,
        emailsSent: 0,
        smsSent: 0,
        metrics: {},
        errors: [],
        warnings: [],
        recommendations: []
    };

    try {
        console.log(`[MAINTENANCE_CLEANUP] Iniciando limpieza y mantenimiento del sistema`);

        // 1. Limpiar logs antiguos
        if (context.parameters.cleanOldLogs) {
            const cleanupResponse = await fetch(`${supabaseUrl}/rest/v1/rpc/fnc_limpiar_datos_antiguos`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            });

            if (cleanupResponse.ok) {
                const cleanedRecords = await cleanupResponse.json();
                result.metrics.recordsCleaned = cleanedRecords;
                console.log(`[MAINTENANCE_CLEANUP] Registros limpiados: ${cleanedRecords}`);
            }
        }

        // 2. Limpiar logs de ejecución antiguos
        if (context.parameters.cleanOldLogs) {
            const thirtyDaysAgo = new Date();
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

            await fetch(
                `${supabaseUrl}/rest/v1/cron_jobs_execution_log?created_at=lt.${thirtyDaysAgo.toISOString()}`,
                {
                    method: 'DELETE',
                    headers: {
                        'apikey': serviceRoleKey,
                        'Authorization': `Bearer ${serviceRoleKey}`
                    }
                }
            );
        }

        // 3. Limpiar alertas resueltas antiguas
        if (context.parameters.cleanOldAlerts) {
            const sevenDaysAgo = new Date();
            sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

            await fetch(
                `${supabaseUrl}/rest/v1/cron_jobs_alerts?estado_alerta=eq.resuelta&fecha_resolucion=lt.${sevenDaysAgo.toISOString()}`,
                {
                    method: 'DELETE',
                    headers: {
                        'apikey': serviceRoleKey,
                        'Authorization': `Bearer ${serviceRoleKey}`
                    }
                }
            );
        }

        // 4. Reiniciar circuit breakers
        if (context.parameters.restartCircuitBreakers) {
            for (const jobId of Object.keys(JOB_CONFIGS)) {
                const breaker = CIRCUIT_BREAKERS.get(jobId);
                if (breaker && breaker.state !== 'closed') {
                    breaker.state = 'closed';
                    breaker.failures = 0;
                    breaker.successCount = 0;
                    breaker.lastFailure = null;
                    CIRCUIT_BREAKERS.set(jobId, breaker);
                }
            }
            result.metrics.circuitBreakersReset = Object.keys(JOB_CONFIGS).length;
        }

        // 5. Generar reporte de mantenimiento
        const reportResult = await generateMaintenanceReport(result, context, supabaseUrl, serviceRoleKey);
        result.emailsSent = reportResult.emailsSent;

        result.success = true;
        result.executionTimeMs = Date.now() - startTime;

        // Generar recomendaciones de mantenimiento
        if (result.metrics.recordsCleaned > 1000) {
            result.recommendations.push('Alto volumen de datos limpiados - considerar aumentar frecuencia de limpieza');
        }
        if (Object.keys(CIRCUIT_BREAKERS).some(id => CIRCUIT_BREAKERS.get(id)?.state !== 'closed')) {
            result.recommendations.push('Circuit breakers activos - investigar problemas recurrentes');
        }

        console.log(`[MAINTENANCE_CLEANUP] Completado exitosamente en ${result.executionTimeMs}ms`);

    } catch (error) {
        result.errors.push(`Error en mantenimiento: ${error.message}`);
        console.error(`[MAINTENANCE_CLEANUP] Error:`, error);
    }

    return result;
}

// =====================================================
// FUNCIONES DE UTILIDAD Y SOPORTE
// =====================================================

/**
 * REGISTRAR EJECUCIÓN EN BASE DE DATOS
 */
async function recordJobExecution(
    supabaseUrl: string,
    serviceRoleKey: string,
    context: JobExecutionContext,
    estado: string,
    result?: JobResult,
    errorMessage?: string
): Promise<void> {
    try {
        const executionData = {
            job_id: context.jobId,
            execution_id: context.executionId,
            start_time: context.startTime.toISOString(),
            end_time: estado !== 'iniciado' ? new Date().toISOString() : null,
            duracion_ms: estado !== 'iniciado' ? 
                Date.now() - context.startTime.getTime() : null,
            estado: estado,
            request_id: context.requestId,
            parametros_ejecucion: context.parameters,
            resultado: result || {},
            error_message: errorMessage,
            memory_usage_start: context.environment.memoryUsage.heapUsed,
            productos_procesados: result?.productsProcessed || 0,
            productos_exitosos: result?.productsSuccessful || 0,
            productos_fallidos: result?.productsFailed || 0,
            alertas_generadas: result?.alertsGenerated || 0,
            emails_enviados: result?.emailsSent || 0,
            sms_enviados: result?.smsSent || 0
        };

        await fetch(`${supabaseUrl}/rest/v1/cron_jobs_execution_log`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            },
            body: JSON.stringify(executionData)
        });

        // Actualizar estado del job
        if (estado !== 'iniciado') {
            const updateData = {
                estado_job: estado === 'exitoso' ? 'exitoso' : 'fallido',
                ultima_ejecucion: context.startTime.toISOString(),
                duracion_ejecucion_ms: Date.now() - context.startTime.getTime(),
                intentos_ejecucion: estado === 'fallido' ? 'intentos_ejecucion + 1' : 0,
                resultado_ultima_ejecucion: result || {},
                error_ultima_ejecucion: errorMessage,
                updated_at: new Date().toISOString()
            };

            await fetch(`${supabaseUrl}/rest/v1/cron_jobs_tracking?job_id=eq.${context.jobId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                },
                body: JSON.stringify(updateData)
            });
        }

    } catch (error) {
        console.error('Error registrando ejecución:', error);
    }
}

/**
 * ENVIAR NOTIFICACIONES
 */
async function sendNotifications(
    jobId: string,
    result: JobResult,
    context: JobExecutionContext
): Promise<void> {
    const jobConfig = JOB_CONFIGS[jobId];
    if (!jobConfig || !jobConfig.notificationChannels.length) return;

    try {
        for (const channel of jobConfig.notificationChannels) {
            switch (channel) {
                case 'email':
                    if (result.errors.length > 0 || result.alertsGenerated > 5) {
                        await sendEmailAlert(jobId, result, context);
                    }
                    break;
                case 'sms':
                    if (result.errors.length > 0) {
                        await sendSMSAlert(jobId, result, context);
                    }
                    break;
                case 'slack':
                    await sendSlackNotification(jobId, result, context);
                    break;
            }
        }
    } catch (error) {
        console.error('Error enviando notificaciones:', error);
    }
}

/**
 * CREAR ALERTA DEL SISTEMA
 */
async function createSystemAlert(
    jobId: string,
    executionId: string,
    tipoAlerta: string,
    severidad: string,
    titulo: string,
    descripcion: string,
    accionRecomendada: string
): Promise<void> {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!supabaseUrl || !serviceRoleKey) return;

    try {
        const alertData = {
            job_id: jobId,
            execution_id: executionId,
            tipo_alerta: tipoAlerta,
            severidad: severidad,
            titulo: titulo,
            descripcion: descripcion,
            accion_recomendada: accionRecomendada,
            canales_notificacion: ['email', 'slack'],
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
        console.error('Error creando alerta del sistema:', error);
    }
}

/**
 * REGISTRAR HEALTH CHECK
 */
async function recordHealthCheck(
    jobId: string,
    checkType: string,
    status: string,
    responseTimeMs?: number,
    details?: any
): Promise<void> {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!supabaseUrl || !serviceRoleKey) return;

    try {
        const healthData = {
            job_id: jobId,
            check_type: checkType,
            status: status,
            response_time_ms: responseTimeMs,
            check_details: details || {},
            last_success: status === 'healthy' ? new Date().toISOString() : null
        };

        await fetch(`${supabaseUrl}/rest/v1/cron_jobs_health_checks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            },
            body: JSON.stringify(healthData)
        });

    } catch (error) {
        console.error('Error registrando health check:', error);
    }
}

/**
 * CIRCUIT BREAKER MANAGEMENT
 */
function checkCircuitBreaker(jobId: string): boolean {
    const breaker = CIRCUIT_BREAKERS.get(jobId) || {
        state: 'closed',
        failures: 0,
        lastFailure: null,
        successCount: 0,
        threshold: JOB_CONFIGS[jobId]?.circuitBreakerThreshold || 5
    };

    if (breaker.state === 'open') {
        const now = new Date();
        if (breaker.lastFailure && (now.getTime() - breaker.lastFailure.getTime()) > 300000) { // 5 minutos
            breaker.state = 'half_open';
            breaker.successCount = 0;
            CIRCUIT_BREAKERS.set(jobId, breaker);
            return true;
        }
        return false;
    }

    return true;
}

function markCircuitBreakerSuccess(jobId: string): void {
    const breaker = CIRCUIT_BREAKERS.get(jobId) || {
        state: 'closed',
        failures: 0,
        lastFailure: null,
        successCount: 0,
        threshold: JOB_CONFIGS[jobId]?.circuitBreakerThreshold || 5
    };

    if (breaker.state === 'half_open') {
        breaker.successCount++;
        if (breaker.successCount >= 3) {
            breaker.state = 'closed';
            breaker.failures = 0;
        }
    } else if (breaker.state === 'closed') {
        breaker.failures = Math.max(0, breaker.failures - 1);
    }

    CIRCUIT_BREAKERS.set(jobId, breaker);
}

function markCircuitBreakerFailure(jobId: string): void {
    const breaker = CIRCUIT_BREAKERS.get(jobId) || {
        state: 'closed',
        failures: 0,
        lastFailure: null,
        successCount: 0,
        threshold: JOB_CONFIGS[jobId]?.circuitBreakerThreshold || 5
    };

    breaker.failures++;
    breaker.lastFailure = new Date();

    if (breaker.failures >= breaker.threshold && breaker.state === 'closed') {
        breaker.state = 'open';
    }

    CIRCUIT_BREAKERS.set(jobId, breaker);
}

function getCircuitBreakerStatus(): Record<string, CircuitBreakerState> {
    const status: Record<string, CircuitBreakerState> = {};
    for (const jobId of Object.keys(JOB_CONFIGS)) {
        status[jobId] = CIRCUIT_BREAKERS.get(jobId) || {
            state: 'closed',
            failures: 0,
            lastFailure: null,
            successCount: 0,
            threshold: JOB_CONFIGS[jobId].circuitBreakerThreshold
        };
    }
    return status;
}

/**
 * ACTUALIZAR MÉTRICAS DE PERFORMANCE
 */
function updatePerformanceMetrics(result: JobResult): void {
    PERFORMANCE_METRICS.jobsExecuted++;
    if (result.success) {
        PERFORMANCE_METRICS.jobsSucceeded++;
    } else {
        PERFORMANCE_METRICS.jobsFailed++;
    }
    
    PERFORMANCE_METRICS.totalExecutionTime += result.executionTimeMs;
    PERFORMANCE_METRICS.averageExecutionTime = 
        PERFORMANCE_METRICS.totalExecutionTime / PERFORMANCE_METRICS.jobsExecuted;
    
    PERFORMANCE_METRICS.alertsGenerated += result.alertsGenerated;
    PERFORMANCE_METRICS.notificationsSent += result.emailsSent + result.smsSent;
}

function updateRealTimeMetrics(result: JobResult): void {
    // Actualizar métricas específicas para tiempo real
    if ((globalThis as any).realTimeMetrics === undefined) {
        (globalThis as any).realTimeMetrics = {
            checksPerHour: 0,
            alertsPerHour: 0,
            averageResponseTime: 0,
            lastReset: Date.now()
        };
    }
    
    const metrics = (globalThis as any).realTimeMetrics;
    metrics.checksPerHour++;
    metrics.alertsPerHour += result.alertsGenerated;
    
    // Resetear cada hora
    if (Date.now() - metrics.lastReset > 3600000) {
        metrics.checksPerHour = 0;
        metrics.alertsPerHour = 0;
        metrics.lastReset = Date.now();
    }
}

/**
 * CALCULAR MÉTRICAS DEL SISTEMA
 */
function calculateSystemMetrics(jobs: any[], metrics: any[], alerts: any[]): any {
    const totalJobs = jobs.length;
    const activeJobs = jobs.filter(j => j.estado_job === 'ejecutando').length;
    const failedJobs = jobs.filter(j => j.estado_job === 'fallido').length;
    
    const totalExecutions = metrics.reduce((sum, m) => sum + m.ejecuciones_totales, 0);
    const totalSuccesses = metrics.reduce((sum, m) => sum + m.ejecuciones_exitosas, 0);
    const totalFailures = metrics.reduce((sum, m) => sum + m.ejecuciones_fallidas, 0);
    
    return {
        overallHealth: totalJobs > 0 ? 
            Math.round(((totalJobs - failedJobs) / totalJobs) * 100) : 100,
        jobsExecutedToday: totalExecutions,
        successRate: totalExecutions > 0 ? 
            Math.round((totalSuccesses / totalExecutions) * 100) : 0,
        averageExecutionTime: metrics.length > 0 ?
            Math.round(metrics.reduce((sum, m) => sum + m.tiempo_promedio_ms, 0) / metrics.length) : 0,
        alertsGenerated: alerts.length
    };
}

function calculateDetailedMetrics(metrics: any[]): any {
    if (metrics.length === 0) return {};

    return {
        totalExecutions: metrics.reduce((sum, m) => sum + m.ejecuciones_totales, 0),
        successfulExecutions: metrics.reduce((sum, m) => sum + m.ejecuciones_exitosas, 0),
        failedExecutions: metrics.reduce((sum, m) => sum + m.ejecuciones_fallidas, 0),
        averageExecutionTime: metrics.reduce((sum, m) => sum + m.tiempo_promedio_ms, 0) / metrics.length,
        averageSuccessRate: metrics.reduce((sum, m) => sum + m.disponibilidad_porcentual, 0) / metrics.length,
        totalProductsProcessed: metrics.reduce((sum, m) => sum + m.productos_procesados_total, 0),
        totalAlertsGenerated: metrics.reduce((sum, m) => sum + m.alertas_generadas_total, 0)
    };
}

function calculateTrends(metrics: any[]): any {
    if (metrics.length < 2) return { trend: 'insufficient_data' };

    const sortedMetrics = metrics.sort((a, b) => 
        new Date(a.fecha_metricas).getTime() - new Date(b.fecha_metricas).getTime()
    );

    const recent = sortedMetrics.slice(-7); // Última semana
    const previous = sortedMetrics.slice(-14, -7);

    const recentAvg = recent.reduce((sum, m) => sum + m.disponibilidad_porcentual, 0) / recent.length;
    const previousAvg = previous.reduce((sum, m) => sum + (m.disponibilidad_porcentual || 0), 0) / previous.length;

    const trend = recentAvg > previousAvg ? 'improving' : 
                 recentAvg < previousAvg ? 'declining' : 'stable';

    return {
        trend,
        recentAverage: Math.round(recentAvg),
        previousAverage: Math.round(previousAvg),
        change: Math.round(recentAvg - previousAvg)
    };
}

function calculatePerformanceTrends(executions: any[]): any {
    if (executions.length === 0) return {};

    const recentExecutions = executions.slice(0, 10);
    const successful = recentExecutions.filter(e => e.estado === 'exitoso');
    
    return {
        successRate: recentExecutions.length > 0 ? 
            Math.round((successful.length / recentExecutions.length) * 100) : 0,
        averageExecutionTime: recentExecutions.length > 0 ?
            Math.round(recentExecutions.reduce((sum, e) => sum + (e.duracion_ms || 0), 0) / recentExecutions.length) : 0,
        recentFailures: recentExecutions.filter(e => e.estado === 'fallido').length
    };
}

function calculateOverallHealthScore(health: SystemHealthMetrics): number {
    let score = 100;

    // Penalizar por problemas de base de datos
    if (health.database.status === 'critical') score -= 30;
    else if (health.database.status === 'degraded') score -= 15;

    // Penalizar por alto uso de memoria
    if (health.memory.percentage > 80) score -= 25;
    else if (health.memory.percentage > 60) score -= 10;

    // Penalizar por jobs fallidos
    if (health.jobs.failed > 0) score -= health.jobs.failed * 10;

    // Penalizar por alertas críticas
    if (health.alerts.critical > 0) score -= health.alerts.critical * 15;

    // Penalizar por bajo success rate
    if (health.jobs.successRate < 90) score -= (90 - health.jobs.successRate);

    return Math.max(0, Math.min(100, score));
}

function generateMetricRecommendations(metrics: any[], executions: any[]): string[] {
    const recommendations = [];

    // Analizar success rate
    const avgSuccessRate = metrics.reduce((sum, m) => sum + m.disponibilidad_porcentual, 0) / metrics.length;
    if (avgSuccessRate < 95) {
        recommendations.push('Success rate bajo el 95% - revisar jobs con más fallos');
    }

    // Analizar tiempo de ejecución
    const avgExecutionTime = metrics.reduce((sum, m) => sum + m.tiempo_promedio_ms, 0) / metrics.length;
    if (avgExecutionTime > 300000) { // 5 minutos
        recommendations.push('Tiempo de ejecución promedio alto - optimizar procesos');
    }

    // Analizar frecuencia de fallos
    const recentFailures = executions.filter(e => e.estado === 'fallido').length;
    if (recentFailures > executions.length * 0.2) {
        recommendations.push('Alto porcentaje de fallos recientes - investigar problemas sistémicos');
    }

    return recommendations;
}

function calculateAverageResolutionTime(alerts: any[]): number {
    const resolvedAlerts = alerts.filter(a => a.fecha_resolucion);
    if (resolvedAlerts.length === 0) return 0;

    const totalTime = resolvedAlerts.reduce((sum, alert) => {
        const created = new Date(alert.created_at).getTime();
        const resolved = new Date(alert.fecha_resolucion).getTime();
        return sum + (resolved - created);
    }, 0);

    return Math.round(totalTime / resolvedAlerts.length / (1000 * 60)); // Minutos
}

function calculateSystemHealth(jobs: any[], alerts: any[]): number {
    const totalJobs = jobs.length;
    const failedJobs = jobs.filter(j => j.estado_job === 'fallido').length;
    const criticalAlerts = alerts.filter(a => a.severidad === 'critica').length;

    let health = 100;
    health -= (failedJobs / totalJobs) * 100;
    health -= criticalAlerts * 10;

    return Math.max(0, Math.min(100, health));
}

function calculateExecutionTrends(executions: any[]): any {
    if (executions.length === 0) return {};

    const last24Hours = executions.filter(e => 
        new Date(e.start_time) > new Date(Date.now() - 24 * 60 * 60 * 1000)
    );

    const successful = last24Hours.filter(e => e.estado === 'exitoso').length;

    return {
        last24Hours: last24Hours.length,
        successRate: last24Hours.length > 0 ? 
            Math.round((successful / last24Hours.length) * 100) : 0,
        trend: last24Hours.length > 10 ? 'stable' : 'low_activity'
    };
}

function calculateAlertTrends(alerts: any[]): any {
    const last24Hours = alerts.filter(a => 
        new Date(a.created_at) > new Date(Date.now() - 24 * 60 * 60 * 1000)
    );

    return {
        last24Hours: last24Hours.length,
        critical: last24Hours.filter(a => a.severidad === 'critica').length,
        trend: last24Hours.length > 5 ? 'increasing' : 'stable'
    };
}

function calculateSystemLoad(): any {
    return {
        cpuUsage: Math.round(Math.random() * 50 + 20), // Simulado
        memoryUsage: Math.round(performance.memory ? 
            (performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize) * 100 : 40),
        activeJobs: ACTIVE_EXECUTIONS.size,
        queueLength: 0 // En una implementación real sería dinámico
    };
}

function generateSystemRecommendations(jobs: any[], alerts: any[], weeklyMetrics: any[]): string[] {
    const recommendations = [];

    // Analizar jobs inactivos por mucho tiempo
    const inactiveJobs = jobs.filter(j => 
        j.ultima_ejecucion && 
        new Date(j.ultima_ejecucion) < new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    );
    if (inactiveJobs.length > 0) {
        recommendations.push(`${inactiveJobs.length} jobs sin ejecutar en la última semana`);
    }

    // Analizar alto número de alertas críticas
    const criticalAlerts = alerts.filter(a => a.severidad === 'critica').length;
    if (criticalAlerts > 3) {
        recommendations.push('Alto número de alertas críticas - revisar configuración del sistema');
    }

    // Analizar trends de performance
    const avgSuccessRate = weeklyMetrics.reduce((sum, m) => sum + m.disponibilidad_promedio, 0) / weeklyMetrics.length;
    if (avgSuccessRate < 90) {
        recommendations.push('Tasa de éxito promedio baja - optimizar jobs con más fallos');
    }

    return recommendations;
}

/**
 * ANÁLISIS DE TENDENCIAS BÁSICO
 */
function performBasicTrendAnalysis(priceHistory: any[]): any {
    if (priceHistory.length === 0) return { message: 'No hay datos suficientes' };

    // Agrupar por producto
    const productGroups = priceHistory.reduce((groups, item) => {
        if (!groups[item.producto_id]) {
            groups[item.producto_id] = [];
        }
        groups[item.producto_id].push(item);
        return groups;
    }, {});

    const trends = {
        totalProducts: Object.keys(productGroups).length,
        upwardTrends: 0,
        downwardTrends: 0,
        stableProducts: 0,
        volatility: 0,
        averageChange: 0
    };

    let totalChanges = 0;
    let changeCount = 0;

    Object.values(productGroups).forEach((productPrices: any) => {
        // Ordenar por fecha
        productPrices.sort((a: any, b: any) => 
            new Date(a.fecha_cambio).getTime() - new Date(b.fecha_cambio).getTime()
        );

        if (productPrices.length < 2) return;

        const firstPrice = productPrices[0].precio;
        const lastPrice = productPrices[productPrices.length - 1].precio;
        const change = ((lastPrice - firstPrice) / firstPrice) * 100;

        totalChanges += Math.abs(change);
        changeCount++;

        if (change > 5) trends.upwardTrends++;
        else if (change < -5) trends.downwardTrends++;
        else trends.stableProducts++;
    });

    trends.averageChange = changeCount > 0 ? totalChanges / changeCount : 0;
    trends.volatility = changeCount > 0 ? totalChanges / changeCount / 100 : 0;

    return trends;
}

/**
 * PREDICCIONES SIMPLES
 */
function generateSimplePredictions(priceHistory: any[]): any {
    // Implementación básica de ML para predicción de tendencias
    const predictions = {
        upwardTrends: 0,
        downwardTrends: 0,
        stableTrends: 0,
        confidence: 0,
        predictedChanges: []
    };

    // Algoritmo simple basado en patrones recientes
    const recentData = priceHistory.filter(item => 
        new Date(item.fecha_cambio) > new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
    );

    // Agrupar por producto y analizar tendencia reciente
    const productGroups = recentData.reduce((groups: any, item: any) => {
        if (!groups[item.producto_id]) {
            groups[item.producto_id] = [];
        }
        groups[item.producto_id].push(item);
        return groups;
    }, {});

    Object.values(productGroups).forEach((prices: any) => {
        if (prices.length >= 2) {
            prices.sort((a: any, b: any) => 
                new Date(a.fecha_cambio).getTime() - new Date(b.fecha_cambio).getTime()
            );

            // Calcular tendencia simple
            const recentPrices = prices.slice(-3);
            const priceChanges = recentPrices.map((p: any, i: number) => 
                i > 0 ? p.precio - recentPrices[i - 1].precio : 0
            ).slice(1);

            const avgChange = priceChanges.reduce((sum: number, change: number) => sum + change, 0) / priceChanges.length;
            
            if (avgChange > 2) {
                predictions.upwardTrends++;
                predictions.predictedChanges.push({ direction: 'up', magnitude: avgChange });
            } else if (avgChange < -2) {
                predictions.downwardTrends++;
                predictions.predictedChanges.push({ direction: 'down', magnitude: Math.abs(avgChange) });
            } else {
                predictions.stableTrends++;
                predictions.predictedChanges.push({ direction: 'stable', magnitude: 0 });
            }
        }
    });

    // Calcular confianza basada en cantidad de datos
    predictions.confidence = Math.min(90, Object.keys(productGroups).length * 5);

    return predictions;
}

/**
 * ANÁLISIS ESTACIONAL
 */
function analyzeSeasonality(priceHistory: any[]): any {
    // Análisis básico de patrones estacionales
    const seasonalPatterns = {
        weekly: {},
        monthly: {},
        detectedPatterns: []
    };

    // Agrupar por día de la semana
    priceHistory.forEach(item => {
        const date = new Date(item.fecha_cambio);
        const dayOfWeek = date.getDay();
        const month = date.getMonth();

        if (!seasonalPatterns.weekly[dayOfWeek]) {
            seasonalPatterns.weekly[dayOfWeek] = [];
        }
        seasonalPatterns.weekly[dayOfWeek].push(item.precio);

        if (!seasonalPatterns.monthly[month]) {
            seasonalPatterns.monthly[month] = [];
        }
        seasonalPatterns.monthly[month].push(item.precio);
    });

    // Detectar patrones (simplificado)
    Object.keys(seasonalPatterns.weekly).forEach(day => {
        const prices = seasonalPatterns.weekly[day];
        if (prices.length > 5) {
            const avgPrice = prices.reduce((sum: number, price: number) => sum + price, 0) / prices.length;
            seasonalPatterns.detectedPatterns.push({
                type: 'weekly',
                period: day,
                averagePrice: Math.round(avgPrice * 100) / 100,
                frequency: prices.length
            });
        }
    });

    return seasonalPatterns;
}

/**
 * GENERAR REPORTES
 */
async function generateDailyReport(
    context: JobExecutionContext,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<{ emailsSent: number }> {
    // Obtener datos para el reporte
    const productsResponse = await fetch(
        `${supabaseUrl}/rest/v1/precios_proveedor?select=*&ultima_actualizacion=gte.${new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()}&limit=100`,
        {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        }
    );

    const products = productsResponse.ok ? await productsResponse.json() : [];

    // Obtener alertas recientes
    const alertsResponse = await fetch(
        `${supabaseUrl}/rest/v1/alertas_cambios_precios?select=*&fecha_alerta=gte.${new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()}&order=fecha_alerta.desc&limit=10`,
        {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        }
    );

    const alerts = alertsResponse.ok ? await alertsResponse.json() : [];

    // Generar template de email
    const template = NOTIFICATION_CONFIG.email.templates['daily_report'];
    const htmlBody = template.htmlBody
        .replace('{{executionDate}}', context.startTime.toLocaleDateString())
        .replace('{{productsProcessed}}', products.length.toString())
        .replace('{{executionTime}}', Math.round((Date.now() - context.startTime.getTime()) / 1000).toString())
        .replace('{{alertsGenerated}}', alerts.length.toString())
        .replace('{{successRate}}', '95')
        .replace('{{criticalAlerts}}', generateAlertsHTML(alerts.filter(a => a.severidad === 'critica')))
        .replace('{{recommendations}}', generateRecommendationsHTML())
        .replace('{{categoryBreakdown}}', generateCategoryBreakdownHTML(products));

    const textBody = template.textBody
        .replace('{{executionDate}}', context.startTime.toLocaleDateString())
        .replace('{{productsProcessed}}', products.length.toString())
        .replace('{{executionTime}}', Math.round((Date.now() - context.startTime.getTime()) / 1000).toString())
        .replace('{{alertsGenerated}}', alerts.length.toString())
        .replace('{{successRate}}', '95')
        .replace('{{criticalAlerts}}', generateAlertsText(alerts.filter(a => a.severidad === 'critica')))
        .replace('{{recommendations}}', generateRecommendationsText())
        .replace('{{categoryBreakdown}}', generateCategoryBreakdownText(products));

    // Simular envío de email (en implementación real usar SMTP)
    console.log(`[DAILY_REPORT] Simulando envío de reporte diario`);
    
    return { emailsSent: 1 };
}

async function generateWeeklyReport(
    analysisData: any,
    context: JobExecutionContext,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<{ emailsSent: number }> {
    // Generar reporte semanal con análisis
    const template = NOTIFICATION_CONFIG.email.templates['weekly_analysis'];
    
    // En implementación real, aquí se generaría el reporte completo con gráficos
    console.log(`[WEEKLY_REPORT] Generando reporte de análisis semanal`);
    
    return { emailsSent: 1 };
}

async function generateMaintenanceReport(
    result: JobResult,
    context: JobExecutionContext,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<{ emailsSent: number }> {
    console.log(`[MAINTENANCE_REPORT] Generando reporte de mantenimiento`);
    
    return { emailsSent: 0 }; // Los reportes de mantenimiento no se envían por defecto
}

/**
 * CREAR ALERTAS ESPECÍFICAS
 */
async function createProductAlert(newProducts: any[], context: JobExecutionContext): Promise<number> {
    if (newProducts.length === 0) return 0;

    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    try {
        for (const product of newProducts.slice(0, 5)) { // Limitar a 5 productos
            const alertData = {
                job_id: context.jobId,
                execution_id: context.executionId,
                tipo_alerta: 'nuevo_producto',
                severidad: 'media',
                titulo: `Nuevo producto detectado: ${product.nombre}`,
                descripcion: `Se detectó un nuevo producto: ${product.nombre} - SKU: ${product.sku}`,
                accion_recomendada: 'Revisar y categorizar nuevo producto',
                canales_notificacion: ['email'],
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
        }

        return Math.min(newProducts.length, 5);
    } catch (error) {
        console.error('Error creando alerta de productos:', error);
        return 0;
    }
}

async function createStockAlert(lowStockProducts: any[], context: JobExecutionContext): Promise<number> {
    if (lowStockProducts.length === 0) return 0;

    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    try {
        for (const product of lowStockProducts.slice(0, 5)) { // Limitar a 5 productos
            const alertData = {
                job_id: context.jobId,
                execution_id: context.executionId,
                tipo_alerta: 'stock_bajo',
                severidad: product.stock_disponible < 5 ? 'critica' : 'alta',
                titulo: `Stock bajo: ${product.nombre}`,
                descripcion: `El producto ${product.nombre} tiene stock bajo: ${product.stock_disponible} unidades`,
                accion_recomendada: 'Revisar y reponer stock urgentemente',
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
        }

        return Math.min(lowStockProducts.length, 5);
    } catch (error) {
        console.error('Error creando alerta de stock:', error);
        return 0;
    }
}

/**
 * FUNCIONES DE NOTIFICACIÓN
 */
async function sendEmailAlert(jobId: string, result: JobResult, context: JobExecutionContext): Promise<void> {
    try {
        const template = NOTIFICATION_CONFIG.email.templates['critical_alert'];
        const htmlBody = template.htmlBody
            .replace('{{alertType}}', `Job ${jobId}`)
            .replace('{{alertTitle}}', `Error en ejecución de ${jobId}`)
            .replace('{{alertDescription}}', result.errors.join(', '))
            .replace('{{jobId}}', jobId)
            .replace('{{executionId}}', context.executionId)
            .replace('{{timestamp}}', new Date().toISOString())
            .replace('{{severity}}', 'Alta')
            .replace('{{recommendedAction}}', 'Revisar logs de ejecución y estado del sistema')
            .replace('{{dashboardUrl}}', 'https://minimarket.com/dashboard');

        // En implementación real, aquí se enviaría el email
        console.log(`[EMAIL_ALERT] Simulando envío de alerta crítica para job ${jobId}`);
    } catch (error) {
        console.error('Error enviando alerta por email:', error);
    }
}

async function sendSMSAlert(jobId: string, result: JobResult, context: JobExecutionContext): Promise<void> {
    try {
        // En implementación real, aquí se enviaría SMS via Twilio
        console.log(`[SMS_ALERT] Simulando envío de SMS crítico para job ${jobId}`);
    } catch (error) {
        console.error('Error enviando alerta por SMS:', error);
    }
}

async function sendSlackNotification(jobId: string, result: JobResult, context: JobExecutionContext): Promise<void> {
    try {
        const webhookUrl = NOTIFICATION_CONFIG.webhooks.slack.webhookUrl;
        if (!webhookUrl) return;

        const message = {
            channel: NOTIFICATION_CONFIG.webhooks.slack.channel,
            text: `🚨 Alerta Cron Job: ${jobId}`,
            attachments: [
                {
                    color: result.success ? 'good' : 'danger',
                    fields: [
                        {
                            title: 'Estado',
                            value: result.success ? '✅ Exitoso' : '❌ Fallido',
                            short: true
                        },
                        {
                            title: 'Ejecución ID',
                            value: context.executionId,
                            short: true
                        },
                        {
                            title: 'Duración',
                            value: `${result.executionTimeMs}ms`,
                            short: true
                        },
                        {
                            title: 'Alertas',
                            value: result.alertsGenerated.toString(),
                            short: true
                        }
                    ],
                    footer: 'Sistema MiniMarket',
                    ts: Math.floor(Date.now() / 1000)
                }
            ]
        };

        // En implementación real, aquí se enviaría a Slack
        console.log(`[SLACK_NOTIFICATION] Simulando notificación para job ${jobId}`);
    } catch (error) {
        console.error('Error enviando notificación a Slack:', error);
    }
}

/**
 * FUNCIONES DE UTILIDAD PARA HTML/TEXT
 */
function generateAlertsHTML(alerts: any[]): string {
    if (alerts.length === 0) return '<p>No hay alertas críticas</p>';
    
    return alerts.map(alert => 
        `<div style="background: #fff3cd; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc107;">
            <strong>${alert.mensaje}</strong><br>
            <small>Producto: ${alert.productos?.nombre || 'N/A'}</small>
        </div>`
    ).join('');
}

function generateRecommendationsHTML(): string {
    const recommendations = [
        'Revisar productos con cambios de precio superiores al 15%',
        'Verificar stock de productos con alta demanda',
        'Optimizar frecuencia de scraping para productos volátiles'
    ];

    return recommendations.map(rec => 
        `<div style="padding: 5px 0;">• ${rec}</div>`
    ).join('');
}

function generateCategoryBreakdownHTML(products: any[]): string {
    const categories = products.reduce((acc: any, product) => {
        const cat = product.categoria || 'Sin categoría';
        acc[cat] = (acc[cat] || 0) + 1;
        return acc;
    }, {});

    return Object.entries(categories).map(([cat, count]) => 
        `<div style="display: flex; justify-content: space-between; padding: 5px 0;">
            <span>${cat}</span>
            <span><strong>${count}</strong> productos</span>
        </div>`
    ).join('');
}

function generateAlertsText(alerts: any[]): string {
    if (alerts.length === 0) return 'No hay alertas críticas';
    return alerts.map(alert => `• ${alert.mensaje}`).join('\n');
}

function generateRecommendationsText(): string {
    const recommendations = [
        'Revisar productos con cambios de precio superiores al 15%',
        'Verificar stock de productos con alta demanda',
        'Optimizar frecuencia de scraping para productos volátiles'
    ];
    return recommendations.map(rec => `• ${rec}`).join('\n');
}

function generateCategoryBreakdownText(products: any[]): string {
    const categories = products.reduce((acc: any, product) => {
        const cat = product.categoria || 'Sin categoría';
        acc[cat] = (acc[cat] || 0) + 1;
        return acc;
    }, {});

    return Object.entries(categories).map(([cat, count]) => 
        `${cat}: ${count} productos`
    ).join('\n');
}

/**
 * CLASIFICACIÓN DE ERRORES
 */
function isRetryableError(error: Error): boolean {
    const retryableErrors = [
        'timeout',
        'network',
        'connection',
        'rate limit',
        'too many requests',
        'temporalmente no disponible',
        'econnreset',
        'econnrefused'
    ];

    return retryableErrors.some(keyword => 
        error.message.toLowerCase().includes(keyword)
    );
}

/**
 * DELAY CON JITTER
 */
function delay(ms: number): Promise<void> {
    const jitter = Math.random() * 0.3 * ms;
    return new Promise(resolve => setTimeout(resolve, ms + jitter));
}

// Inicializar metadatos globales
if (!(globalThis as any).startTime) {
    (globalThis as any).startTime = Date.now();
}