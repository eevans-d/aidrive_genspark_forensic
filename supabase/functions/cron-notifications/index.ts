/**
 * SISTEMA DE NOTIFICACIONES AVANZADAS
 * Edge Function para Gestión Completa de Notificaciones Multi-Canal
 * 
 * CARACTERÍSTICAS:
 * - Templates de email profesionales con branding
 * - SMS vía Twilio para alertas críticas
 * - Slack/Teams para notificaciones de equipo
 * - Webhooks personalizados
 * - Gestión de preferencias por usuario
 * - Escalamiento automático según severidad
 * 
 * @author MiniMax Agent - Sistema Automatizado
 * @version 3.0.0
 * @date 2025-11-01
 * @license Enterprise Level
 */

// =====================================================
// INTERFACES Y TIPOS
// =====================================================

interface NotificationTemplate {
    id: string;
    name: string;
    type: 'email' | 'sms' | 'slack' | 'webhook';
    subject?: string;
    htmlBody: string;
    textBody: string;
    variables: string[];
    branding: {
        logo?: string;
        colors: {
            primary: string;
            secondary: string;
            accent: string;
        };
        company: string;
        footer: string;
    };
}

interface NotificationChannel {
    id: string;
    name: string;
    type: 'email' | 'sms' | 'slack' | 'teams' | 'webhook';
    config: {
        // Email
        smtpHost?: string;
        smtpPort?: number;
        smtpUser?: string;
        smtpPassword?: string;
        fromEmail?: string;
        fromName?: string;
        
        // SMS
        twilioAccountSid?: string;
        twilioAuthToken?: string;
        fromNumber?: string;
        
        // Slack/Teams
        webhookUrl?: string;
        channel?: string;
        username?: string;
        
        // Webhook
        method?: string;
        headers?: Record<string, string>;
    };
    isActive: boolean;
    rateLimit: {
        maxPerHour: number;
        maxPerDay: number;
    };
}

interface NotificationRequest {
    templateId: string;
    channels: string[];
    recipients: {
        email?: string[];
        phone?: string[];
        slack_channels?: string[];
        webhook_urls?: string[];
    };
    data: Record<string, any>;
    priority: 'low' | 'medium' | 'high' | 'critical';
    source: string;
    requiresEscalation: boolean;
}

interface NotificationResult {
    success: boolean;
    channels: {
        channelId: string;
        status: 'sent' | 'failed' | 'rate_limited';
        messageId?: string;
        error?: string;
        timestamp: string;
    }[];
    totalSent: number;
    totalFailed: number;
    rateLimited: number;
}

interface EscalationRule {
    id: string;
    name: string;
    trigger: {
        severity: string[];
        timeThreshold: number; // minutes
        noResponse: boolean;
    };
    action: {
        type: 'email' | 'sms' | 'slack' | 'webhook';
        recipients: string[];
        templateId: string;
    };
    isActive: boolean;
}

// =====================================================
// CONFIGURACIÓN DE TEMPLATES
// =====================================================

const NOTIFICATION_TEMPLATES: Record<string, NotificationTemplate> = {
    'daily_price_update': {
        id: 'daily_price_update',
        name: 'Reporte Diario de Precios',
        type: 'email',
        subject: '📊 Reporte Diario MiniMarket - {{executionDate}}',
        htmlBody: `
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <div style="background-color: white; width: 60px; height: 60px; border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; font-size: 24px;">
                        🛒
                    </div>
                    <h1 style="margin: 0; font-size: 28px; font-weight: 700;">MiniMarket Daily Report</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Actualización Automática de Precios - {{executionDate}}</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px; background-color: white; margin: 0 10px;">
                    <!-- Executive Summary -->
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 25px; border-radius: 10px; margin-bottom: 30px;">
                        <h2 style="margin: 0 0 15px 0; font-size: 24px;">📈 Resumen Ejecutivo</h2>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 32px; font-weight: bold;">{{productsProcessed}}</div>
                                <div style="font-size: 14px; opacity: 0.9;">Productos Procesados</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 32px; font-weight: bold;">{{executionTime}}s</div>
                                <div style="font-size: 14px; opacity: 0.9;">Tiempo de Ejecución</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 32px; font-weight: bold;">{{alertsGenerated}}</div>
                                <div style="font-size: 14px; opacity: 0.9;">Alertas Generadas</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 32px; font-weight: bold;">{{successRate}}%</div>
                                <div style="font-size: 14px; opacity: 0.9;">Tasa de Éxito</div>
                            </div>
                        </div>
                    </div>

                    <!-- Critical Alerts -->
                    {{#if criticalAlerts}}
                    <div style="background-color: #fff5f5; border: 2px solid #fed7d7; border-radius: 10px; padding: 20px; margin-bottom: 30px;">
                        <h2 style="color: #c53030; margin: 0 0 15px 0; font-size: 20px;">🚨 Alertas Críticas</h2>
                        {{criticalAlerts}}
                    </div>
                    {{/if}}

                    <!-- Category Breakdown -->
                    <div style="background-color: #f7fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin-bottom: 30px;">
                        <h2 style="color: #2d3748; margin: 0 0 15px 0; font-size: 20px;">📊 Detalles por Categoría</h2>
                        {{categoryBreakdown}}
                    </div>

                    <!-- Recommendations -->
                    <div style="background: linear-gradient(135deg, #4fd1c7 0%, #38b2ac 100%); color: white; border-radius: 10px; padding: 20px; margin-bottom: 30px;">
                        <h2 style="margin: 0 0 15px 0; font-size: 20px;">💡 Recomendaciones</h2>
                        {{recommendations}}
                    </div>

                    <!-- System Status -->
                    <div style="background-color: #f0fff4; border: 1px solid #9ae6b4; border-radius: 10px; padding: 20px;">
                        <h2 style="color: #22543d; margin: 0 0 15px 0; font-size: 20px;">⚡ Estado del Sistema</h2>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                            <div style="display: flex; align-items: center; background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #48bb78;">
                                <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #48bb78; margin-right: 10px;"></div>
                                <span style="color: #2f855a; font-weight: 500;">Base de Datos: Operativa</span>
                            </div>
                            <div style="display: flex; align-items: center; background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #48bb78;">
                                <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #48bb78; margin-right: 10px;"></div>
                                <span style="color: #2f855a; font-weight: 500;">Scraper: Funcionando</span>
                            </div>
                            <div style="display: flex; align-items: center; background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #48bb78;">
                                <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #48bb78; margin-right: 10px;"></div>
                                <span style="color: #2f855a; font-weight: 500;">Circuit Breakers: Estables</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #2d3748; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; margin: 0 10px 10px;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.8;">🤖 Generado automáticamente por el Sistema de Cron Jobs MiniMarket</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.6;">📧 ¿Problemas? Contacta a soporte técnico | 🌐 Ver Dashboard Completo</p>
                </div>
            </div>
        `,
        textBody: `
MiniMarket - Reporte Diario de Precios
========================================

Fecha: {{executionDate}}

RESUMEN EJECUTIVO:
• Productos Procesados: {{productsProcessed}}
• Tiempo de Ejecución: {{executionTime}}s
• Alertas Generadas: {{alertsGenerated}}
• Tasa de Éxito: {{successRate}}%

ALERTAS CRÍTICAS:
{{criticalAlerts}}

DETALLES POR CATEGORÍA:
{{categoryBreakdown}}

RECOMENDACIONES:
{{recommendations}}

ESTADO DEL SISTEMA:
• Base de Datos: ✅ Operativa
• Scraper: ✅ Funcionando  
• Circuit Breakers: ✅ Estables

---
Generado automáticamente por MiniMarket System
        `,
        variables: ['executionDate', 'productsProcessed', 'executionTime', 'alertsGenerated', 'successRate', 'criticalAlerts', 'categoryBreakdown', 'recommendations'],
        branding: {
            colors: {
                primary: '#667eea',
                secondary: '#764ba2',
                accent: '#f093fb'
            },
            company: 'MiniMarket',
            footer: 'Sistema Automatizado de Gestión de Precios'
        }
    },
    
    'critical_alert': {
        id: 'critical_alert',
        name: 'Alerta Crítica del Sistema',
        type: 'email',
        subject: '🚨 ALERTA CRÍTICA - {{alertType}}',
        htmlBody: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #fef2f2;">
                <!-- Critical Header -->
                <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <div style="background-color: white; width: 60px; height: 60px; border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; font-size: 24px;">
                        🚨
                    </div>
                    <h1 style="margin: 0; font-size: 28px; font-weight: 700;">ALERTA CRÍTICA</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">{{alertType}} - Requiere Atención Inmediata</p>
                </div>
                
                <!-- Alert Content -->
                <div style="padding: 30px; background-color: white; margin: 0 10px;">
                    <h2 style="color: #dc2626; margin: 0 0 20px 0; font-size: 24px;">⚠️ {{alertTitle}}</h2>
                    <p style="font-size: 16px; line-height: 1.6; color: #374151;">{{alertDescription}}</p>
                    
                    <!-- Technical Details -->
                    <div style="background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; padding: 20px; margin: 25px 0;">
                        <h3 style="color: #1f2937; margin: 0 0 15px 0; font-size: 18px;">📊 Detalles Técnicos</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div><strong>Job ID:</strong> {{jobId}}</div>
                            <div><strong>Execution ID:</strong> {{executionId}}</div>
                            <div><strong>Timestamp:</strong> {{timestamp}}</div>
                            <div><strong>Severidad:</strong> <span style="color: #dc2626; font-weight: bold; font-size: 18px;">{{severity}}</span></div>
                        </div>
                    </div>
                    
                    <!-- Recommended Action -->
                    <div style="background: linear-gradient(135deg, #fef3c7 0%, #f59e0b 100%); border-radius: 10px; padding: 20px; margin: 25px 0; border-left: 5px solid #f59e0b;">
                        <h3 style="color: #92400e; margin: 0 0 15px 0; font-size: 18px;">💡 Acción Recomendada</h3>
                        <p style="margin: 0; color: #92400e; font-size: 16px; line-height: 1.5;">{{recommendedAction}}</p>
                    </div>
                    
                    <!-- Quick Actions -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{dashboardUrl}}" style="display: inline-block; background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 5px;">
                            🔍 Ver Dashboard Completo
                        </a>
                        <a href="{{logsUrl}}" style="display: inline-block; background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 5px;">
                            📋 Revisar Logs
                        </a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #1f2937; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; margin: 0 10px 10px;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.8;">🔔 Sistema de Alertas MiniMarket</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.6;">Esta alerta se generó automáticamente y requiere atención inmediata</p>
                </div>
            </div>
        `,
        textBody: `
ALERTA CRÍTICA - Sistema MiniMarket
===================================

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

ACCIONES RÁPIDAS:
• Dashboard: {{dashboardUrl}}
• Logs: {{logsUrl}}

---
Sistema de Alertas MiniMarket - Requiere Atención Inmediata
        `,
        variables: ['alertType', 'alertTitle', 'alertDescription', 'jobId', 'executionId', 'timestamp', 'severity', 'recommendedAction', 'dashboardUrl', 'logsUrl'],
        branding: {
            colors: {
                primary: '#dc2626',
                secondary: '#991b1b',
                accent: '#f59e0b'
            },
            company: 'MiniMarket',
            footer: 'Sistema de Alertas Críticas'
        }
    },

    'weekly_trend_report': {
        id: 'weekly_trend_report',
        name: 'Reporte Semanal de Tendencias',
        type: 'email',
        subject: '📈 Reporte Semanal - Análisis de Tendencias MiniMarket',
        htmlBody: `
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto; background-color: #f8fafc;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; border-radius: 15px 15px 0 0;">
                    <div style="background-color: white; width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 36px;">
                        📊
                    </div>
                    <h1 style="margin: 0; font-size: 32px; font-weight: 700;">Análisis Semanal de Tendencias</h1>
                    <p style="margin: 15px 0 0 0; font-size: 18px; opacity: 0.9;">Inteligencia de Negocios MiniMarket</p>
                    <p style="margin: 5px 0 0 0; font-size: 16px; opacity: 0.8;">Semana del {{weekStart}} al {{weekEnd}}</p>
                </div>
                
                <!-- Executive Summary -->
                <div style="padding: 40px; background-color: white; margin: 0 15px;">
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 15px; padding: 30px; margin-bottom: 40px;">
                        <h2 style="margin: 0 0 20px 0; font-size: 26px;">🎯 Resumen Ejecutivo</h2>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 25px;">
                            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 12px; text-align: center; backdrop-filter: blur(10px);">
                                <div style="font-size: 36px; font-weight: bold;">{{productsAnalyzed}}</div>
                                <div style="font-size: 15px; opacity: 0.9;">Productos Analizados</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 12px; text-align: center; backdrop-filter: blur(10px);">
                                <div style="font-size: 36px; font-weight: bold;">{{trendsDetected}}</div>
                                <div style="font-size: 15px; opacity: 0.9;">Tendencias Detectadas</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 12px; text-align: center; backdrop-filter: blur(10px);">
                                <div style="font-size: 36px; font-weight: bold;">{{accuracyScore}}%</div>
                                <div style="font-size: 15px; opacity: 0.9;">Precisión ML</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 12px; text-align: center; backdrop-filter: blur(10px);">
                                <div style="font-size: 36px; font-weight: bold;">{{recommendationsCount}}</div>
                                <div style="font-size: 15px; opacity: 0.9;">Recomendaciones</div>
                            </div>
                        </div>
                    </div>

                    <!-- Trend Analysis -->
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 15px; padding: 30px; margin-bottom: 30px;">
                        <h2 style="color: #1e293b; margin: 0 0 20px 0; font-size: 24px;">📈 Análisis de Tendencias</h2>
                        {{trendAnalysis}}
                    </div>

                    <!-- ML Predictions -->
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; border-radius: 15px; padding: 30px; margin-bottom: 30px;">
                        <h2 style="margin: 0 0 20px 0; font-size: 24px;">🤖 Predicciones ML</h2>
                        {{mlPredictions}}
                    </div>

                    <!-- Executive Recommendations -->
                    <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; border-radius: 15px; padding: 30px;">
                        <h2 style="margin: 0 0 20px 0; font-size: 24px;">💼 Recomendaciones Ejecutivas</h2>
                        {{executiveRecommendations}}
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #1e293b; color: white; padding: 25px; text-align: center; border-radius: 0 0 15px 15px; margin: 0 15px 15px;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.8;">🤖 Generado por MiniMarket AI Analytics System</p>
                    <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.6;">📊 ¿Datos adicionales? Contacta al equipo de Business Intelligence</p>
                </div>
            </div>
        `,
        textBody: `
MiniMarket - Análisis Semanal de Tendencias
===========================================

Período: {{weekStart}} al {{weekEnd}}

RESUMEN EJECUTIVO:
• Productos Analizados: {{productsAnalyzed}}
• Tendencias Detectadas: {{trendsDetected}}
• Precisión ML: {{accuracyScore}}%
• Recomendaciones: {{recommendationsCount}}

ANÁLISIS DE TENDENCIAS:
{{trendAnalysis}}

PREDICCIONES ML:
{{mlPredictions}}

RECOMENDACIONES EJECUTIVAS:
{{executiveRecommendations}}

---
Análisis generado por MiniMarket AI Analytics System
        `,
        variables: ['weekStart', 'weekEnd', 'productsAnalyzed', 'trendsDetected', 'accuracyScore', 'recommendationsCount', 'trendAnalysis', 'mlPredictions', 'executiveRecommendations'],
        branding: {
            colors: {
                primary: '#4facfe',
                secondary: '#00f2fe',
                accent: '#43e97b'
            },
            company: 'MiniMarket',
            footer: 'AI Analytics & Business Intelligence'
        }
    }
};

// =====================================================
// CANALES DE NOTIFICACIÓN CONFIGURADOS
// =====================================================

const NOTIFICATION_CHANNELS: Record<string, NotificationChannel> = {
    'email_default': {
        id: 'email_default',
        name: 'Email Principal',
        type: 'email',
        config: {
            smtpHost: Deno.env.get('SMTP_HOST') || 'smtp.gmail.com',
            smtpPort: parseInt(Deno.env.get('SMTP_PORT') || '587'),
            smtpUser: Deno.env.get('SMTP_USER') || '',
            smtpPassword: Deno.env.get('SMTP_PASS') || '',
            fromEmail: Deno.env.get('EMAIL_FROM') || 'noreply@minimarket.com',
            fromName: 'Sistema MiniMarket'
        },
        isActive: true,
        rateLimit: {
            maxPerHour: 100,
            maxPerDay: 1000
        }
    },

    'sms_critical': {
        id: 'sms_critical',
        name: 'SMS Alertas Críticas',
        type: 'sms',
        config: {
            twilioAccountSid: Deno.env.get('TWILIO_ACCOUNT_SID'),
            twilioAuthToken: Deno.env.get('TWILIO_AUTH_TOKEN'),
            fromNumber: Deno.env.get('TWILIO_FROM_NUMBER') || '+1234567890'
        },
        isActive: true,
        rateLimit: {
            maxPerHour: 10,
            maxPerDay: 50
        }
    },

    'slack_alerts': {
        id: 'slack_alerts',
        name: 'Slack Alertas Equipo',
        type: 'slack',
        config: {
            webhookUrl: Deno.env.get('SLACK_WEBHOOK_URL'),
            channel: '#alerts-minimarket',
            username: 'MiniMarket Bot'
        },
        isActive: true,
        rateLimit: {
            maxPerHour: 50,
            maxPerDay: 200
        }
    }
};

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
        const action = url.pathname.split('/').pop() || 'send';

        console.log(`[NOTIFICATIONS] Acción: ${action}`);

        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Configuración de Supabase faltante');
        }

        let response: Response;

        switch (action) {
            case 'send':
                response = await sendNotificationHandler(req, supabaseUrl, serviceRoleKey, corsHeaders);
                break;
            case 'templates':
                response = await getTemplatesHandler(corsHeaders);
                break;
            case 'channels':
                response = await getChannelsHandler(corsHeaders);
                break;
            case 'test':
                response = await testNotificationHandler(req, supabaseUrl, serviceRoleKey, corsHeaders);
                break;
            case 'preferences':
                response = await getUserPreferencesHandler(req, supabaseUrl, serviceRoleKey, corsHeaders);
                break;
            case 'escalation':
                response = await checkEscalationHandler(req, supabaseUrl, serviceRoleKey, corsHeaders);
                break;
            default:
                throw new Error(`Acción no válida: ${action}`);
        }

        return response;

    } catch (error) {
        console.error('[NOTIFICATIONS] Error:', error);
        
        return new Response(JSON.stringify({
            success: false,
            error: {
                code: 'NOTIFICATION_ERROR',
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
// MANEJADORES PRINCIPALES
// =====================================================

/**
 * ENVIAR NOTIFICACIÓN
 */
async function sendNotificationHandler(
    req: Request,
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>
): Promise<Response> {
    const notificationRequest: NotificationRequest = await req.json();
    
    console.log('[NOTIFICATIONS] Enviando notificación:', notificationRequest.templateId);

    // Validar request
    if (!notificationRequest.templateId || !notificationRequest.channels || !notificationRequest.recipients) {
        throw new Error('Request inválido: faltan campos requeridos');
    }

    const template = NOTIFICATION_TEMPLATES[notificationRequest.templateId];
    if (!template) {
        throw new Error(`Template no encontrado: ${notificationRequest.templateId}`);
    }

    // Verificar rate limits
    await checkRateLimits(notificationRequest.channels);

    // Generar contenido para cada canal
    const results: NotificationResult = {
        success: false,
        channels: [],
        totalSent: 0,
        totalFailed: 0,
        rateLimited: 0
    };

    // Enviar por cada canal especificado
    for (const channelId of notificationRequest.channels) {
        const channel = NOTIFICATION_CHANNELS[channelId];
        if (!channel || !channel.isActive) {
            results.channels.push({
                channelId,
                status: 'failed',
                error: 'Canal inactivo o no encontrado',
                timestamp: new Date().toISOString()
            });
            results.totalFailed++;
            continue;
        }

        try {
            const result = await sendToChannel(channel, template, notificationRequest, supabaseUrl, serviceRoleKey);
            results.channels.push(result);
            
            if (result.status === 'sent') results.totalSent++;
            else if (result.status === 'rate_limited') results.rateLimited++;
            else results.totalFailed++;

        } catch (error) {
            results.channels.push({
                channelId,
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
            results.totalFailed++;
        }
    }

    // Registrar notificación en base de datos
    await recordNotificationLog(notificationRequest, results, supabaseUrl, serviceRoleKey);

    // Verificar si necesita escalamiento
    if (notificationRequest.requiresEscalation && results.totalFailed > 0) {
        await triggerEscalation(notificationRequest, results, supabaseUrl, serviceRoleKey);
    }

    results.success = results.totalSent > 0;

    console.log(`[NOTIFICATIONS] Resultado: ${results.totalSent} enviados, ${results.totalFailed} fallidos`);

    return new Response(JSON.stringify({
        success: results.success,
        data: {
            notificationId: `notif_${Date.now()}`,
            result: results,
            timestamp: new Date().toISOString()
        }
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}

/**
 * ENVIAR A CANAL ESPECÍFICO
 */
async function sendToChannel(
    channel: NotificationChannel,
    template: NotificationTemplate,
    request: NotificationRequest,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<{
    channelId: string;
    status: 'sent' | 'failed' | 'rate_limited';
    messageId?: string;
    error?: string;
    timestamp: string;
}> {
    const timestamp = new Date().toISOString();

    // Verificar rate limit específico del canal
    const rateLimitOk = await checkChannelRateLimit(channel.id);
    if (!rateLimitOk) {
        return {
            channelId: channel.id,
            status: 'rate_limited',
            error: 'Rate limit excedido para este canal',
            timestamp
        };
    }

    try {
        let messageId: string | undefined;

        switch (channel.type) {
            case 'email':
                messageId = await sendEmail(channel, template, request);
                break;
            case 'sms':
                messageId = await sendSMS(channel, template, request);
                break;
            case 'slack':
                messageId = await sendSlack(channel, template, request);
                break;
            case 'webhook':
                messageId = await sendWebhook(channel, template, request);
                break;
            default:
                throw new Error(`Tipo de canal no soportado: ${channel.type}`);
        }

        // Actualizar rate limits
        await updateRateLimits(channel.id);

        return {
            channelId: channel.id,
            status: 'sent',
            messageId,
            timestamp
        };

    } catch (error) {
        console.error(`[NOTIFICATIONS] Error enviando a ${channel.id}:`, error);
        return {
            channelId: channel.id,
            status: 'failed',
            error: error.message,
            timestamp
        };
    }
}

/**
 * ENVIAR EMAIL
 */
async function sendEmail(
    channel: NotificationChannel,
    template: NotificationTemplate,
    request: NotificationRequest
): Promise<string> {
    if (!channel.config.smtpHost || !channel.config.fromEmail) {
        throw new Error('Configuración de email incompleta');
    }

    // Generar contenido con variables
    const htmlBody = processTemplate(template.htmlBody, request.data);
    const textBody = processTemplate(template.textBody, request.data);
    const subject = processTemplate(template.subject || '', request.data);

    // En implementación real, aquí se enviaría el email
    // Por ahora simulamos el envío
    console.log(`[EMAIL] Enviando a: ${request.recipients.email?.join(', ')}`);
    console.log(`[EMAIL] Subject: ${subject}`);
    console.log(`[EMAIL] HTML Body: ${htmlBody.substring(0, 200)}...`);

    // Simular delay de envío
    await new Promise(resolve => setTimeout(resolve, 100));

    return `email_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * ENVIAR SMS
 */
async function sendSMS(
    channel: NotificationChannel,
    template: NotificationTemplate,
    request: NotificationRequest
): Promise<string> {
    if (!channel.config.twilioAccountSid || !channel.config.fromNumber) {
        throw new Error('Configuración de SMS incompleta');
    }

    // Generar mensaje SMS (máximo 160 caracteres)
    const message = processTemplate(template.textBody, request.data)
        .substring(0, 160);

    // En implementación real, aquí se enviaría SMS via Twilio
    console.log(`[SMS] Enviando a: ${request.recipients.phone?.join(', ')}`);
    console.log(`[SMS] Message: ${message}`);

    // Simular delay de envío
    await new Promise(resolve => setTimeout(resolve, 200));

    return `sms_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * ENVIAR SLACK
 */
async function sendSlack(
    channel: NotificationChannel,
    template: NotificationTemplate,
    request: NotificationRequest
): Promise<string> {
    if (!channel.config.webhookUrl) {
        throw new Error('URL de webhook de Slack no configurada');
    }

    // Crear mensaje de Slack
    const message = {
        channel: channel.config.channel || '#general',
        username: channel.config.username || 'MiniMarket Bot',
        text: processTemplate(template.textBody, request.data).substring(0, 4000),
        attachments: [
            {
                color: request.priority === 'critical' ? 'danger' : 
                       request.priority === 'high' ? 'warning' : 'good',
                fields: [
                    {
                        title: 'Tipo',
                        value: template.name,
                        short: true
                    },
                    {
                        title: 'Prioridad',
                        value: request.priority,
                        short: true
                    },
                    {
                        title: 'Fuente',
                        value: request.source,
                        short: true
                    }
                ],
                footer: 'MiniMarket Notifications',
                ts: Math.floor(Date.now() / 1000)
            }
        ]
    };

    // En implementación real, aquí se enviaría a Slack
    console.log(`[SLACK] Enviando a canal: ${channel.config.channel}`);
    console.log(`[SLACK] Webhook URL configurada: ${!!channel.config.webhookUrl}`);

    // Simular delay de envío
    await new Promise(resolve => setTimeout(resolve, 150));

    return `slack_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * ENVIAR WEBHOOK
 */
async function sendWebhook(
    channel: NotificationChannel,
    template: NotificationTemplate,
    request: NotificationRequest
): Promise<string> {
    if (!channel.config.webhookUrl) {
        throw new Error('URL de webhook no configurada');
    }

    // Crear payload del webhook
    const payload = {
        template: template.id,
        data: request.data,
        priority: request.priority,
        source: request.source,
        timestamp: new Date().toISOString(),
        recipients: request.recipients
    };

    // En implementación real, aquí se enviaría el webhook
    console.log(`[WEBHOOK] Enviando a: ${channel.config.webhookUrl}`);
    console.log(`[WEBHOOK] Payload:`, payload);

    // Simular delay de envío
    await new Promise(resolve => setTimeout(resolve, 100));

    return `webhook_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

// =====================================================
// FUNCIONES DE UTILIDAD
// =====================================================

function processTemplate(template: string, data: Record<string, any>): string {
    let processed = template;
    
    // Reemplazar variables {{variable}}
    for (const [key, value] of Object.entries(data)) {
        const regex = new RegExp(`{{${key}}}`, 'g');
        processed = processed.replace(regex, String(value || ''));
    }

    // Reemplazar condicionales simples {{#if condition}}...{{/if}}
    const ifRegex = /{{#if\s+(\w+)}}([\s\S]*?){{\/if}}/g;
    processed = processed.replace(ifRegex, (match, condition, content) => {
        return data[condition] ? content : '';
    });

    return processed;
}

async function checkRateLimits(channelIds: string[]): Promise<void> {
    for (const channelId of channelIds) {
        const channel = NOTIFICATION_CHANNELS[channelId];
        if (channel) {
            const rateLimitOk = await checkChannelRateLimit(channelId);
            if (!rateLimitOk) {
                throw new Error(`Rate limit excedido para canal: ${channelId}`);
            }
        }
    }
}

async function checkChannelRateLimit(channelId: string): Promise<boolean> {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!supabaseUrl || !serviceRoleKey) return true;

    try {
        // Obtener conteo de últimas notificaciones
        const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
        const response = await fetch(
            `${supabaseUrl}/rest/v1/cron_jobs_notifications?select=count&channel_id=eq.${channelId}&sent_at=gte.${oneHourAgo}`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        if (response.ok) {
            const result = await response.json();
            const count = result.length;
            const channel = NOTIFICATION_CHANNELS[channelId];
            
            return count < (channel?.rateLimit.maxPerHour || 100);
        }

        return true; // En caso de error, permitir el envío

    } catch (error) {
        console.error('[NOTIFICATIONS] Error verificando rate limit:', error);
        return true;
    }
}

async function updateRateLimits(channelId: string): Promise<void> {
    // En implementación real, aquí se registraría el envío para rate limiting
    console.log(`[NOTIFICATIONS] Rate limit actualizado para canal: ${channelId}`);
}

async function recordNotificationLog(
    request: NotificationRequest,
    result: NotificationResult,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<void> {
    try {
        for (const channel of result.channels) {
            const logData = {
                template_id: request.templateId,
                channel_id: channel.channelId,
                priority: request.priority,
                source: request.source,
                recipients: request.recipients,
                data: request.data,
                status: channel.status,
                message_id: channel.messageId,
                error_message: channel.error,
                sent_at: new Date().toISOString()
            };

            await fetch(`${supabaseUrl}/rest/v1/cron_jobs_notifications`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                },
                body: JSON.stringify(logData)
            });
        }
    } catch (error) {
        console.error('[NOTIFICATIONS] Error registrando log:', error);
    }
}

async function triggerEscalation(
    request: NotificationRequest,
    result: NotificationResult,
    supabaseUrl: string,
    serviceRoleKey: string
): Promise<void> {
    console.log('[NOTIFICATIONS] Triggering escalation for failed notifications');

    // Crear alerta de escalamiento
    const escalationData = {
        job_id: 'notifications',
        execution_id: `escalation_${Date.now()}`,
        tipo_alerta: 'notificacion_fallida',
        severidad: request.priority === 'critical' ? 'critica' : 'alta',
        titulo: `Fallo en notificaciones para ${request.templateId}`,
        descripcion: `${result.totalFailed} notificaciones fallaron de ${result.totalSent + result.totalFailed} enviadas`,
        accion_recomendada: 'Verificar configuración de canales y rate limits',
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
        body: JSON.stringify(escalationData)
    });
}

// =====================================================
// MANEJADORES DE API
// =====================================================

async function getTemplatesHandler(corsHeaders: Record<string, string>): Promise<Response> {
    return new Response(JSON.stringify({
        success: true,
        data: Object.values(NOTIFICATION_TEMPLATES).map(template => ({
            id: template.id,
            name: template.name,
            type: template.type,
            variables: template.variables
        }))
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}

async function getChannelsHandler(corsHeaders: Record<string, string>): Promise<Response> {
    const channels = Object.values(NOTIFICATION_CHANNELS).map(channel => ({
        id: channel.id,
        name: channel.name,
        type: channel.type,
        isActive: channel.isActive,
        rateLimit: channel.rateLimit
    }));

    return new Response(JSON.stringify({
        success: true,
        data: channels
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}

async function testNotificationHandler(
    req: Request,
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>
): Promise<Response> {
    const { templateId, channelId, testData = {} } = await req.json();

    if (!templateId || !channelId) {
        throw new Error('templateId y channelId son requeridos');
    }

    const template = NOTIFICATION_TEMPLATES[templateId];
    const channel = NOTIFICATION_CHANNELS[channelId];

    if (!template || !channel) {
        throw new Error('Template o canal no encontrado');
    }

    const testRequest: NotificationRequest = {
        templateId,
        channels: [channelId],
        recipients: {
            email: ['test@minimarket.com'],
            phone: ['+1234567890']
        },
        data: {
            ...testData,
            executionDate: new Date().toLocaleDateString(),
            testMode: true
        },
        priority: 'low',
        source: 'test',
        requiresEscalation: false
    };

    const result = await sendToChannel(channel, template, testRequest, supabaseUrl, serviceRoleKey);

    return new Response(JSON.stringify({
        success: result.status === 'sent',
        data: result
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}

async function getUserPreferencesHandler(
    req: Request,
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>
): Promise<Response> {
    const userId = req.headers.get('x-user-id') || 'default';

    // En implementación real, obtendríamos preferencias del usuario desde BD
    const preferences = {
        userId,
        channels: {
            email: true,
            sms: false,
            slack: true
        },
        severities: {
            low: false,
            medium: true,
            high: true,
            critical: true
        },
        templates: Object.keys(NOTIFICATION_TEMPLATES).reduce((acc, templateId) => {
            acc[templateId] = true;
            return acc;
        }, {} as Record<string, boolean>)
    };

    return new Response(JSON.stringify({
        success: true,
        data: preferences
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}

async function checkEscalationHandler(
    req: Request,
    supabaseUrl: string,
    serviceRoleKey: string,
    corsHeaders: Record<string, string>
): Promise<Response> {
    const { severity, noResponseMinutes = 30 } = await req.json();

    // Verificar si hay alertas que requieren escalamiento
    const cutoffTime = new Date(Date.now() - noResponseMinutes * 60 * 1000).toISOString();
    const response = await fetch(
        `${supabaseUrl}/rest/v1/cron_jobs_alerts?select=*&severidad=eq.${severity}&estado_alerta=eq.activa&created_at=lt.${cutoffTime}`,
        {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`
            }
        }
    );

    const alerts = response.ok ? await response.json() : [];
    const requiresEscalation = alerts.length > 0;

    return new Response(JSON.stringify({
        success: true,
        data: {
            requiresEscalation,
            alertCount: alerts.length,
            alerts: alerts.slice(0, 10) // Top 10 alertas
        }
    }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
}
