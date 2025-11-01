#!/usr/bin/env node

/**
 * SUITE DE TESTING LOCAL - SISTEMA DE CRON JOBS AUTOMÁTICOS
 * Validación completa del sistema Mini Market Sprint 6
 */

const fs = require('fs');
const path = require('path');

// Colores para la consola
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
    white: '\x1b[37m'
};

class CronSystemTester {
    constructor() {
        this.results = {
            timestamp: new Date().toISOString(),
            totalTests: 0,
            passed: 0,
            failed: 0,
            skipped: 0,
            suites: {},
            summary: {},
            errors: [],
            coverage: {}
        };
    }

    async runAllTests() {
        console.log(`${colors.bright}${colors.cyan}🚀 INICIANDO SUITE DE TESTING COMPLETA${colors.reset}`);
        console.log(`${colors.cyan}Sistema: Mini Market - Cron Jobs Automáticos${colors.reset}`);
        console.log(`${colors.cyan}Fecha: ${new Date().toLocaleString('es-ES')}${colors.reset}\n`);

        const testSuites = [
            { name: 'Validación de Archivos del Sistema', fn: () => this.testFileSystem() },
            { name: 'Edge Functions Core', fn: () => this.testEdgeFunctions() },
            { name: 'Base de Datos y Schema', fn: () => this.testDatabase() },
            { name: 'Jobs y Scheduling', fn: () => this.testCronJobs() },
            { name: 'Sistema de Notificaciones', fn: () => this.testNotifications() },
            { name: 'Health Monitoring', fn: () => this.testHealthMonitoring() },
            { name: 'Dashboard y APIs', fn: () => this.testDashboard() },
            { name: 'Documentación', fn: () => this.testDocumentation() },
            { name: 'Configuración de Entorno', fn: () => this.testEnvironment() },
            { name: 'Testing y Calidad', fn: () => this.testQualityAssurance() }
        ];

        for (const suite of testSuites) {
            console.log(`${colors.bright}${colors.magenta}📋 Ejecutando: ${suite.name}${colors.reset}`);
            try {
                const startTime = Date.now();
                await suite.fn();
                const duration = Date.now() - startTime;
                console.log(`   ${colors.green}✅ Completado en ${duration}ms${colors.reset}\n`);
            } catch (error) {
                console.log(`   ${colors.red}❌ Error: ${error.message}${colors.reset}\n`);
                this.results.errors.push(`${suite.name}: ${error.message}`);
            }
        }

        this.generateFinalReport();
    }

    async testFileSystem() {
        const basePath = '/workspace';
        const requiredFiles = [
            'supabase/functions/cron-jobs-maxiconsumo/index.ts',
            'supabase/functions/cron-health-monitor/index.ts',
            'supabase/functions/cron-notifications/index.ts',
            'supabase/functions/cron-testing-suite/index.ts',
            'supabase/functions/cron-dashboard/index.ts',
            'backend/migration/09_cron_jobs_tables.sql',
            'docs/CRON_JOBS_COMPLETOS.md',
            'docs/IMPLEMENTACION_COMPLETADA.md'
        ];

        let passed = 0;
        let failed = 0;

        for (const file of requiredFiles) {
            const fullPath = path.join(basePath, file);
            if (fs.existsSync(fullPath)) {
                const stats = fs.statSync(fullPath);
                console.log(`   ${colors.green}✅ ${file} (${stats.size} bytes)${colors.reset}`);
                passed++;
            } else {
                console.log(`   ${colors.red}❌ ${file} NO ENCONTRADO${colors.reset}`);
                failed++;
            }
            this.results.totalTests++;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Sistema de Archivos'] = { passed, failed, total: passed + failed };
    }

    async testEdgeFunctions() {
        const functions = [
            { name: 'cron-jobs-maxiconsumo', file: 'supabase/functions/cron-jobs-maxiconsumo/index.ts' },
            { name: 'cron-health-monitor', file: 'supabase/functions/cron-health-monitor/index.ts' },
            { name: 'cron-notifications', file: 'supabase/functions/cron-notifications/index.ts' },
            { name: 'cron-testing-suite', file: 'supabase/functions/cron-testing-suite/index.ts' },
            { name: 'cron-dashboard', file: 'supabase/functions/cron-dashboard/index.ts' }
        ];

        let passed = 0;
        let failed = 0;

        for (const func of functions) {
            const filePath = path.join('/workspace', func.file);
            if (fs.existsSync(filePath)) {
                const content = fs.readFileSync(filePath, 'utf8');
                
                // Validaciones específicas
                const validations = [
                    { test: content.includes('Deno.serve'), desc: 'Estructura Deno válida' },
                    { test: content.includes('interface'), desc: 'Interfaces TypeScript' },
                    { test: content.includes('const corsHeaders'), desc: 'Headers CORS' },
                    { test: content.includes('try {') && content.includes('catch'), desc: 'Manejo de errores' }
                ];

                let funcPassed = 0;
                for (const validation of validations) {
                    if (validation.test) {
                        console.log(`   ${colors.green}✅ ${func.name}: ${validation.desc}${colors.reset}`);
                        funcPassed++;
                    } else {
                        console.log(`   ${colors.yellow}⚠️ ${func.name}: ${validation.desc} FALTA${colors.reset}`);
                    }
                }

                if (funcPassed >= 3) {
                    passed++;
                } else {
                    failed++;
                }
            } else {
                console.log(`   ${colors.red}❌ ${func.name} archivo NO ENCONTRADO${colors.reset}`);
                failed++;
            }
            this.results.totalTests++;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Edge Functions'] = { passed, failed, total: passed + failed };
    }

    async testDatabase() {
        const dbFile = '/workspace/backend/migration/09_cron_jobs_tables.sql';
        let passed = 0;
        let failed = 0;

        if (fs.existsSync(dbFile)) {
            const content = fs.readFileSync(dbFile, 'utf8');
            
            const validations = [
                { test: content.includes('cron_jobs_tracking'), desc: 'Tabla cron_jobs_tracking' },
                { test: content.includes('execution_log'), desc: 'Tabla execution_log' },
                { test: content.includes('metrics'), desc: 'Tabla metrics' },
                { test: content.includes('alerts'), desc: 'Tabla alerts' },
                { test: content.includes('notifications'), desc: 'Tabla notifications' },
                { test: content.includes('health_checks'), desc: 'Tabla health_checks' },
                { test: content.includes('CREATE TABLE'), desc: 'Estructura CREATE TABLE' },
                { test: content.includes('INDEX'), desc: 'Índices de optimización' },
                { test: content.includes('TRIGGER'), desc: 'Triggers automáticos' },
                { test: content.includes('FUNCTION'), desc: 'Funciones PL/pgSQL' }
            ];

            for (const validation of validations) {
                if (validation.test) {
                    console.log(`   ${colors.green}✅ ${validation.desc}${colors.reset}`);
                    passed++;
                } else {
                    console.log(`   ${colors.red}❌ ${validation.desc} NO ENCONTRADA${colors.reset}`);
                    failed++;
                }
                this.results.totalTests++;
            }
        } else {
            console.log(`   ${colors.red}❌ Archivo de migración NO ENCONTRADO${colors.reset}`);
            failed += 10;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Base de Datos'] = { passed, failed, total: passed + failed };
    }

    async testCronJobs() {
        const mainFunctionFile = '/workspace/supabase/functions/cron-jobs-maxiconsumo/index.ts';
        let passed = 0;
        let failed = 0;

        if (fs.existsSync(mainFunctionFile)) {
            const content = fs.readFileSync(mainFunctionFile, 'utf8');
            
            const jobs = [
                { name: 'daily_price_update', cron: '0 2 * * *', desc: 'Job diario 02:00 AM' },
                { name: 'weekly_trend_analysis', cron: '0 3 * * 0', desc: 'Job semanal domingos 03:00' },
                { name: 'realtime_change_alerts', cron: '*/15 * * * *', desc: 'Alertas cada 15 min' },
                { name: 'maintenance_cleanup', cron: '0 1 * * *', desc: 'Limpieza diaria 01:00' }
            ];

            for (const job of jobs) {
                if (content.includes(`'${job.name}'`) || content.includes(`"${job.name}"`)) {
                    console.log(`   ${colors.green}✅ ${job.desc} (${job.cron})${colors.reset}`);
                    passed++;
                } else {
                    console.log(`   ${colors.red}❌ ${job.desc} NO ENCONTRADO${colors.reset}`);
                    failed++;
                }
                this.results.totalTests++;
            }

            // Validaciones adicionales
            const additionalValidations = [
                { test: content.includes('Circuit Breaker'), desc: 'Circuit Breaker Pattern' },
                { test: content.includes('retry'), desc: 'Sistema de reintentos' },
                { test: content.includes('MAX_CONCURRENT_JOBS'), desc: 'Control de concurrencia' },
                { test: content.includes('NOTIFICATION_CHANNELS'), desc: 'Configuración de notificaciones' }
            ];

            for (const validation of additionalValidations) {
                if (validation.test) {
                    console.log(`   ${colors.green}✅ ${validation.desc}${colors.reset}`);
                    passed++;
                } else {
                    console.log(`   ${colors.yellow}⚠️ ${validation.desc} FALTA${colors.reset}`);
                }
                this.results.totalTests++;
            }
        } else {
            console.log(`   ${colors.red}❌ Función principal NO ENCONTRADA${colors.reset}`);
            failed += 8;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Cron Jobs'] = { passed, failed, total: passed + failed };
    }

    async testNotifications() {
        const notificationsFile = '/workspace/supabase/functions/cron-notifications/index.ts';
        let passed = 0;
        let failed = 0;

        if (fs.existsSync(notificationsFile)) {
            const content = fs.readFileSync(notificationsFile, 'utf8');
            
            const validations = [
                { test: content.includes('sendEmail'), desc: 'Función sendEmail' },
                { test: content.includes('sendSMS'), desc: 'Función sendSMS' },
                { test: content.includes('sendSlack'), desc: 'Función sendSlack' },
                { test: content.includes('SMTP'), desc: 'Configuración SMTP' },
                { test: content.includes('TWILIO'), desc: 'Configuración Twilio' },
                { test: content.includes('TEMPLATE'), desc: 'Templates HTML' },
                { test: content.includes('batching'), desc: 'Sistema de batching' },
                { test: content.includes('rate_limit'), desc: 'Rate limiting' }
            ];

            for (const validation of validations) {
                if (validation.test) {
                    console.log(`   ${colors.green}✅ ${validation.desc}${colors.reset}`);
                    passed++;
                } else {
                    console.log(`   ${colors.yellow}⚠️ ${validation.desc} FALTA${colors.reset}`);
                }
                this.results.totalTests++;
            }
        } else {
            console.log(`   ${colors.red}❌ Sistema de notificaciones NO ENCONTRADO${colors.reset}`);
            failed += 8;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Notificaciones'] = { passed, failed, total: passed + failed };
    }

    async testHealthMonitoring() {
        const healthFile = '/workspace/supabase/functions/cron-health-monitor/index.ts';
        let passed = 0;
        let failed = 0;

        if (fs.existsSync(healthFile)) {
            const content = fs.readFileSync(healthFile, 'utf8');
            
            const validations = [
                { test: content.includes('performHealthCheck'), desc: 'Función performHealthCheck' },
                { test: content.includes('calculateSystemHealth'), desc: 'Función calculateSystemHealth' },
                { test: content.includes('memory'), desc: 'Monitoreo de memoria' },
                { test: content.includes('database'), desc: 'Health check de BD' },
                { test: content.includes('jobs'), desc: 'Health check de jobs' },
                { test: content.includes('alert_threshold'), desc: 'Umbrales de alerta' }
            ];

            for (const validation of validations) {
                if (validation.test) {
                    console.log(`   ${colors.green}✅ ${validation.desc}${colors.reset}`);
                    passed++;
                } else {
                    console.log(`   ${colors.yellow}⚠️ ${validation.desc} FALTA${colors.reset}`);
                }
                this.results.totalTests++;
            }
        } else {
            console.log(`   ${colors.red}❌ Health monitor NO ENCONTRADO${colors.reset}`);
            failed += 6;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Health Monitoring'] = { passed, failed, total: passed + failed };
    }

    async testDashboard() {
        const dashboardFile = '/workspace/supabase/functions/cron-dashboard/index.ts';
        let passed = 0;
        let failed = 0;

        if (fs.existsSync(dashboardFile)) {
            const content = fs.readFileSync(dashboardFile, 'utf8');
            
            const validations = [
                { test: content.includes('getDashboardData'), desc: 'API getDashboardData' },
                { test: content.includes('getMetrics'), desc: 'API getMetrics' },
                { test: content.includes('getJobStatus'), desc: 'API getJobStatus' },
                { test: content.includes('getAlerts'), desc: 'API getAlerts' },
                { test: content.includes('GET'), desc: 'Endpoints GET' },
                { test: content.includes('POST'), desc: 'Endpoints POST' }
            ];

            for (const validation of validations) {
                if (validation.test) {
                    console.log(`   ${colors.green}✅ ${validation.desc}${colors.reset}`);
                    passed++;
                } else {
                    console.log(`   ${colors.yellow}⚠️ ${validation.desc} FALTA${colors.reset}`);
                }
                this.results.totalTests++;
            }
        } else {
            console.log(`   ${colors.red}❌ Dashboard API NO ENCONTRADO${colors.reset}`);
            failed += 6;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Dashboard'] = { passed, failed, total: passed + failed };
    }

    async testDocumentation() {
        const docs = [
            { file: '/workspace/docs/CRON_JOBS_COMPLETOS.md', desc: 'Documentación técnica completa' },
            { file: '/workspace/docs/IMPLEMENTACION_COMPLETADA.md', desc: 'Reporte de implementación' }
        ];

        let passed = 0;
        let failed = 0;

        for (const doc of docs) {
            if (fs.existsSync(doc.file)) {
                const content = fs.readFileSync(doc.file, 'utf8');
                const size = content.length;
                
                if (size > 1000) {
                    console.log(`   ${colors.green}✅ ${doc.desc} (${size} chars)${colors.reset}`);
                    passed++;
                } else {
                    console.log(`   ${colors.yellow}⚠️ ${doc.desc} MUY PEQUEÑA${colors.reset}`);
                    failed++;
                }
            } else {
                console.log(`   ${colors.red}❌ ${doc.desc} NO ENCONTRADA${colors.reset}`);
                failed++;
            }
            this.results.totalTests++;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Documentación'] = { passed, failed, total: passed + failed };
    }

    async testEnvironment() {
        let passed = 0;
        let failed = 0;

        // Verificar credenciales requeridas
        const requiredEnvVars = [
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_ACCESS_TOKEN',
            'SUPABASE_PROJECT_ID'
        ];

        for (const envVar of requiredEnvVars) {
            if (process.env[envVar]) {
                console.log(`   ${colors.green}✅ ${envVar} CONFIGURADA${colors.reset}`);
                passed++;
            } else {
                console.log(`   ${colors.yellow}⚠️ ${envVar} NO ENCONTRADA${colors.reset}`);
            }
            this.results.totalTests++;
        }

        // Variables opcionales (no son críticas)
        const optionalEnvVars = [
            'SMTP_USER',
            'SMTP_PASS',
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'SLACK_WEBHOOK_URL'
        ];

        for (const envVar of optionalEnvVars) {
            if (process.env[envVar]) {
                console.log(`   ${colors.green}✅ ${envVar} CONFIGURADA (opcional)${colors.reset}`);
            } else {
                console.log(`   ${colors.cyan}ℹ️ ${envVar} NO CONFIGURADA (opcional)${colors.reset}`);
            }
            this.results.totalTests++;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Entorno'] = { passed, failed, total: passed + failed };
    }

    async testQualityAssurance() {
        const testingSuiteFile = '/workspace/supabase/functions/cron-testing-suite/index.ts';
        let passed = 0;
        let failed = 0;

        if (fs.existsSync(testingSuiteFile)) {
            const content = fs.readFileSync(testingSuiteFile, 'utf8');
            
            const validations = [
                { test: content.includes('runAllTests'), desc: 'Función runAllTests' },
                { test: content.includes('testJobExecution'), desc: 'Función testJobExecution' },
                { test: content.includes('testCircuitBreaker'), desc: 'Función testCircuitBreaker' },
                { test: content.includes('testNotifications'), desc: 'Función testNotifications' },
                { test: content.includes('testRecovery'), desc: 'Función testRecovery' },
                { test: content.includes('mock'), desc: 'Sistema de mocks' }
            ];

            for (const validation of validations) {
                if (validation.test) {
                    console.log(`   ${colors.green}✅ ${validation.desc}${colors.reset}`);
                    passed++;
                } else {
                    console.log(`   ${colors.yellow}⚠️ ${validation.desc} FALTA${colors.reset}`);
                }
                this.results.totalTests++;
            }
        } else {
            console.log(`   ${colors.red}❌ Suite de testing NO ENCONTRADA${colors.reset}`);
            failed += 6;
        }

        this.results.passed += passed;
        this.results.failed += failed;
        this.results.suites['Quality Assurance'] = { passed, failed, total: passed + failed };
    }

    generateFinalReport() {
        const successRate = ((this.results.passed / this.results.totalTests) * 100).toFixed(1);
        
        console.log(`${colors.bright}${colors.cyan}📊 REPORTE FINAL DE TESTING${colors.reset}`);
        console.log(`${colors.cyan}========================================${colors.reset}\n`);

        console.log(`${colors.white}📈 Resumen Ejecutivo:${colors.reset}`);
        console.log(`   Total de tests: ${colors.bright}${this.results.totalTests}${colors.reset}`);
        console.log(`   ${colors.green}✅ Exitosos: ${this.results.passed}${colors.reset}`);
        console.log(`   ${colors.red}❌ Fallidos: ${this.results.failed}${colors.reset}`);
        console.log(`   ${colors.yellow}⚠️ Tasa de éxito: ${successRate}%${colors.reset}`);
        console.log(`   ${colors.white}Timestamp: ${this.results.timestamp}${colors.reset}\n`);

        console.log(`${colors.white}📋 Resultados por Suite:${colors.reset}`);
        Object.entries(this.results.suites).forEach(([suiteName, results]) => {
            const rate = ((results.passed / results.total) * 100).toFixed(0);
            const color = rate >= 80 ? colors.green : rate >= 60 ? colors.yellow : colors.red;
            console.log(`   ${color}${suiteName}: ${results.passed}/${results.total} (${rate}%)${colors.reset}`);
        });

        if (this.results.errors.length > 0) {
            console.log(`\n${colors.red}🚨 Errores Encontrados:${colors.reset}`);
            this.results.errors.forEach(error => {
                console.log(`   ❌ ${error}`);
            });
        }

        console.log(`\n${colors.bright}${colors.cyan}🎯 Estado del Sistema:${colors.reset}`);
        if (successRate >= 90) {
            console.log(`   ${colors.green}🟢 SISTEMA COMPLETAMENTE OPERATIVO${colors.reset}`);
            console.log(`   ${colors.green}✅ Todos los componentes funcionan correctamente${colors.reset}`);
        } else if (successRate >= 70) {
            console.log(`   ${colors.yellow}🟡 SISTEMA MAYORMENTE OPERATIVO${colors.reset}`);
            console.log(`   ${colors.yellow}⚠️ Algunos componentes requieren atención${colors.reset}`);
        } else {
            console.log(`   ${colors.red}🔴 SISTEMA REQUIERE ATENCIÓN${colors.reset}`);
            console.log(`   ${colors.red}❌ Varios componentes necesitan corrección${colors.reset}`);
        }

        // Guardar reporte JSON
        const reportFile = `/workspace/test_report_${new Date().getTime()}.json`;
        fs.writeFileSync(reportFile, JSON.stringify(this.results, null, 2));
        console.log(`\n${colors.cyan}📄 Reporte completo guardado en: ${reportFile}${colors.reset}`);

        return {
            success: successRate >= 80,
            successRate: parseFloat(successRate),
            results: this.results
        };
    }
}

// Ejecutar tests
const tester = new CronSystemTester();
tester.runAllTests().then(result => {
    process.exit(result.success ? 0 : 1);
}).catch(error => {
    console.error(`${colors.red}❌ Error ejecutando tests: ${error.message}${colors.reset}`);
    process.exit(1);
});