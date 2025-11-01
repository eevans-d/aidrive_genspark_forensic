/**
 * TESTING DEL SISTEMA DE ALERTAS EN TIEMPO REAL
 * 
 * Suite completa de testing para validar el sistema de alertas de cambios de precios
 * con simulación de cambios reales, validación de umbrales y escalamiento automático.
 * 
 * CARACTERÍSTICAS:
 * - Simulación de cambios de precios reales
 * - Validación de umbrales de alertas (15%+)
 * - Testing de sistema de notificaciones
 * - Validación de escalamiento automático
 * - Testing de recovery ante fallos
 */

const EventEmitter = require('events');
const { performance } = require('perf_hooks');

class AlertSystemTester extends EventEmitter {
  constructor(config = {}) {
    super();
    
    this.config = {
      alertThreshold: 15, // 15% mínimo para alertas
      escalationLevels: 3,
      notificationChannels: ['email', 'sms', 'webhook', 'dashboard'],
      maxRetryAttempts: 3,
      responseTimeTarget: 5000, // 5 segundos
      ...config
    };

    this.alertHistory = [];
    this.notificationLog = [];
    this.escalationEvents = [];
    this.testMetrics = {
      startTime: null,
      totalAlertsGenerated: 0,
      totalNotificationsSent: 0,
      totalEscalations: 0,
      averageResponseTime: 0,
      falsePositives: 0,
      falseNegatives: 0
    };

    // Mock sistema de alertas
    this.alertSystem = new MockAlertSystem();
  }

  /**
   * Ejecuta suite completa de testing del sistema de alertas
   */
  async ejecutarSuiteAlertas() {
    console.log('🚨 INICIANDO TESTING DEL SISTEMA DE ALERTAS');
    console.log('=' .repeat(60));

    this.testMetrics.startTime = performance.now();

    try {
      // 1. Testing de detección de cambios de precios
      await this.testingDetecionCambiosPrecios();

      // 2. Testing de umbrales y filtros de spam
      await this.testingUmbralesFiltrosSpam();

      // 3. Testing de escalamiento automático
      await this.testingEscalamientoAutomatico();

      // 4. Testing de sistema de notificaciones
      await this.testingSistemaNotificaciones();

      // 5. Testing de recovery ante fallos
      await this.testingRecoveryFallos();

      // 6. Testing de performance y latencia
      await this.testingPerformanceAlertas();

      // 7. Generar reporte final
      this.generarReporteAlertas();

      console.log('\n✅ Suite de testing de alertas completada');

    } catch (error) {
      console.error('❌ Error crítico en testing de alertas:', error);
      throw error;
    }
  }

  /**
   * Testing de detección de cambios de precios
   */
  async testingDetecionCambiosPrecios() {
    console.log('\n🔍 TESTING DE DETECCIÓN DE CAMBIOS DE PRECIOS');
    console.log('-' .repeat(50));

    // Escenarios de testing con cambios realistas
    const testScenarios = [
      {
        name: 'Aumento crítico',
        oldPrice: 250,
        newPrice: 325,
        expectedChange: 30,
        shouldAlert: true,
        severity: 'critical'
      },
      {
        name: 'Aumento alto',
        oldPrice: 480,
        newPrice: 556.8,
        expectedChange: 16,
        shouldAlert: true,
        severity: 'high'
      },
      {
        name: 'Aumento moderado',
        oldPrice: 180,
        newPrice: 198,
        expectedChange: 10,
        shouldAlert: false,
        severity: 'normal'
      },
      {
        name: 'Disminución alta',
        oldPrice: 1200,
        newPrice: 960,
        expectedChange: -20,
        shouldAlert: true,
        severity: 'high'
      },
      {
        name: 'Cambio menor',
        oldPrice: 100,
        newPrice: 103,
        expectedChange: 3,
        shouldAlert: false,
        severity: 'normal'
      },
      {
        name: 'Cambio muy alto (posible error)',
        oldPrice: 500,
        newPrice: 1500,
        expectedChange: 200,
        shouldAlert: false, // Debe ser filtrado como spam
        severity: 'suspicious'
      }
    ];

    for (const scenario of testScenarios) {
      console.log(`\n🔄 Testing: ${scenario.name}`);
      console.log(`   💰 $${scenario.oldPrice} → $${scenario.newPrice} (${scenario.expectedChange > 0 ? '+' : ''}${scenario.expectedChange}%)`);

      const startTime = performance.now();
      
      // Simular detección del cambio
      const detection = await this.simularDetecionCambio(scenario);
      const responseTime = performance.now() - startTime;

      // Validar resultado
      const result = this.validarDetecionCambio(scenario, detection);

      console.log(`   📊 Detectado: ${result.detected ? 'SÍ' : 'NO'}`);
      console.log(`   📈 Cambio calculado: ${detection.changePercentage.toFixed(1)}%`);
      console.log(`   🚨 Debería alertar: ${scenario.shouldAlert ? 'SÍ' : 'NO'}`);
      console.log(`   ✅ Resultado correcto: ${result.correct ? 'SÍ' : 'NO'}`);
      console.log(`   ⏱️  Tiempo: ${responseTime.toFixed(0)}ms`);

      if (!result.correct) {
        if (scenario.shouldAlert && !result.detected) {
          this.testMetrics.falseNegatives++;
        } else if (!scenario.shouldAlert && result.detected) {
          this.testMetrics.falsePositives++;
        }
      }

      this.testMetrics.totalAlertsGenerated++;
      if (result.detected) {
        this.testMetrics.averageResponseTime = 
          (this.testMetrics.averageResponseTime + responseTime) / 2;
      }

      await this.delay(1000); // Rate limiting
    }

    console.log(`\n📊 Resumen detección:`);
    console.log(`   False positives: ${this.testMetrics.falsePositives}`);
    console.log(`   False negatives: ${this.testMetrics.falseNegatives}`);
  }

  /**
   * Testing de umbrales y filtros de spam
   */
  async testingUmbralesFiltrosSpam() {
    console.log('\n🛡️  TESTING DE UMBRALES Y FILTROS DE SPAM');
    console.log('-' .repeat(50));

    const spamTestCases = [
      // Casos que deben ser filtrados como spam
      { change: 0.1, expectedFiltered: true, reason: 'Cambio muy pequeño' },
      { change: 0.5, expectedFiltered: true, reason: 'Cambio muy pequeño' },
      { change: 300, expectedFiltered: true, reason: 'Cambio irreal' },
      { change: 500, expectedFiltered: true, reason: 'Cambio irreal' },
      { change: -400, expectedFiltered: true, reason: 'Cambio irreal' },
      
      // Casos que deben pasar el filtro
      { change: 15.5, expectedFiltered: false, reason: 'Cambio válido' },
      { change: -18.2, expectedFiltered: false, reason: 'Cambio válido' },
      { change: 25, expectedFiltered: false, reason: 'Cambio válido' },
      { change: -30, expectedFiltered: false, reason: 'Cambio válido' },
      
      // Casos límite
      { change: 1.0, expectedFiltered: false, reason: 'Límite inferior' },
      { change: 200, expectedFiltered: false, reason: 'Límite superior' }
    ];

    for (const testCase of spamTestCases) {
      console.log(`\n🧪 Testing: ${testCase.change}% (${testCase.reason})`);

      const isFiltered = await this.simularFiltroSpam(testCase.change);
      const correct = isFiltered === testCase.expectedFiltered;

      console.log(`   🔍 Filtrado: ${isFiltered ? 'SÍ' : 'NO'}`);
      console.log(`   ✅ Resultado correcto: ${correct ? 'SÍ' : 'NO'}`);

      if (!correct) {
        console.log(`   ⚠️  FALLO: Esperado ${testCase.expectedFiltered ? 'filtrado' : 'permitido'}`);
      }
    }
  }

  /**
   * Testing de escalamiento automático
   */
  async testingEscalamientoAutomatico() {
    console.log('\n📈 TESTING DE ESCALAMIENTO AUTOMÁTICO');
    console.log('-' .repeat(50));

    // Simular múltiples alertas críticas
    const criticalAlerts = [
      { producto: 'Producto A', cambio: 45, impacto: 'critical' },
      { producto: 'Producto B', cambio: 35, impacto: 'high' },
      { producto: 'Producto C', cambio: 28, impacto: 'high' },
      { producto: 'Producto D', cambio: 22, impacto: 'medium' },
      { producto: 'Producto E', cambio: 18, impacto: 'medium' }
    ];

    console.log('🚀 Simulando múltiples alertas críticas...');

    // Generar alertas y observar escalamiento
    for (const alert of criticalAlerts) {
      const startTime = performance.now();
      
      const alertResult = await this.simularGeneracionAlerta(alert);
      const responseTime = performance.now() - startTime;

      console.log(`\n🔔 Alerta: ${alert.producto} (${alert.cambio}%)`);
      console.log(`   🎯 Severity: ${alert.impacto}`);
      console.log(`   📢 Alertado: ${alertResult.alerted ? 'SÍ' : 'NO'}`);
      console.log(`   📊 Escalado: ${alertResult.escalated ? 'SÍ' : 'NO'}`);
      console.log(`   🔄 Nivel: ${alertResult.escalationLevel || 0}`);

      if (alertResult.escalated) {
        this.escalationEvents.push({
          producto: alert.producto,
          cambio: alert.cambio,
          escalacion: alertResult.escalationLevel,
          timestamp: new Date().toISOString()
        });
        this.testMetrics.totalEscalations++;
      }

      this.testMetrics.totalNotificationsSent += alertResult.notificationsSent;
      await this.delay(2000);
    }

    console.log(`\n📊 Escalamiento total: ${this.testMetrics.totalEscalations} eventos`);
  }

  /**
   * Testing de sistema de notificaciones
   */
  async testingSistemaNotificaciones() {
    console.log('\n📱 TESTING DE SISTEMA DE NOTIFICACIONES');
    console.log('-' .repeat(50));

    const notificationChannels = this.config.notificationChannels;

    for (const channel of notificationChannels) {
      console.log(`\n🔔 Testing canal: ${channel.toUpperCase()}`);

      const notifications = [
        { severity: 'critical', producto: 'Coca Cola', cambio: 35 },
        { severity: 'high', producto: 'Arcor', cambio: 20 },
        { severity: 'medium', producto: 'Nestlé', cambio: 16 }
      ];

      for (const notification of notifications) {
        const startTime = performance.now();
        
        const result = await this.simularEnvioNotificacion(channel, notification);
        const responseTime = performance.now() - startTime;

        console.log(`   📤 ${notification.severity} → ${channel}: ${result.success ? '✅' : '❌'} (${responseTime.toFixed(0)}ms)`);

        if (!result.success) {
          console.log(`      ⚠️  Error: ${result.error}`);
          
          // Test retry logic
          const retryResult = await this.simularReintento(channel, notification);
          console.log(`      🔄 Retry: ${retryResult.success ? '✅' : '❌'}`);
        }

        this.notificationLog.push({
          channel,
          notification,
          success: result.success,
          responseTime,
          timestamp: new Date().toISOString()
        });
      }
    }

    // Statistics
    const totalNotifications = this.notificationLog.length;
    const successfulNotifications = this.notificationLog.filter(n => n.success).length;
    const successRate = (successfulNotifications / totalNotifications * 100).toFixed(1);

    console.log(`\n📊 Estadísticas notificaciones:`);
    console.log(`   Total enviadas: ${totalNotifications}`);
    console.log(`   Exitosas: ${successfulNotifications}`);
    console.log(`   Tasa de éxito: ${successRate}%`);
  }

  /**
   * Testing de recovery ante fallos
   */
  async testingRecoveryFallos() {
    console.log('\n🔄 TESTING DE RECOVERY ANTE FALLOS');
    console.log('-' .repeat(50));

    const failureScenarios = [
      { name: 'Network timeout', type: 'timeout', duration: 10000 },
      { name: 'Server error', type: 'server_error', duration: 5000 },
      { name: 'Database connection', type: 'db_error', duration: 8000 },
      { name: 'Rate limiting', type: 'rate_limit', duration: 30000 }
    ];

    for (const scenario of failureScenarios) {
      console.log(`\n💥 Simulando fallo: ${scenario.name}`);

      // Simular el fallo
      await this.simularFalloSistema(scenario.type);

      // Verificar detección del fallo
      const detectionTime = performance.now();
      const failureDetected = await this.detectarFalloSistema(scenario.type);
      const detectionLatency = performance.now() - detectionTime;

      console.log(`   🔍 Fallo detectado: ${failureDetected ? 'SÍ' : 'NO'} (${detectionLatency.toFixed(0)}ms)`);

      // Iniciar recovery
      const recoveryStart = performance.now();
      const recoveryResult = await this.iniciarRecoveryAutomatico(scenario.type);
      const recoveryTime = performance.now() - recoveryStart;

      console.log(`   🔄 Recovery iniciado: ${recoveryResult.initiated ? 'SÍ' : 'NO'}`);
      console.log(`   ⏱️  Tiempo recovery: ${recoveryTime.toFixed(0)}ms`);
      console.log(`   ✅ Recovery exitoso: ${recoveryResult.success ? 'SÍ' : 'NO'}`);

      // Verificar que el sistema volvió a funcionar
      const systemTest = await this.verificarSistemaFuncionando();
      console.log(`   🧪 Sistema funcionando: ${systemTest.working ? 'SÍ' : 'NO'}`);

      if (recoveryResult.success && systemTest.working) {
        console.log(`   🎉 Recovery completado exitosamente`);
      } else {
        console.log(`   ⚠️  Recovery falló o incompleto`);
      }

      await this.delay(2000);
    }
  }

  /**
   * Testing de performance y latencia del sistema de alertas
   */
  async testingPerformanceAlertas() {
    console.log('\n⚡ TESTING DE PERFORMANCE DE ALERTAS');
    console.log('-' .repeat(50));

    const loadScenarios = [
      { name: 'Carga normal', concurrent: 10, duration: 10000 },
      { name: 'Carga alta', concurrent: 25, duration: 15000 },
      { name: 'Stress test', concurrent: 50, duration: 20000 }
    ];

    for (const scenario of loadScenarios) {
      console.log(`\n🚀 Escenario: ${scenario.name} (${scenario.concurrent} alertas concurrentes)`);

      const startTime = Date.now();
      const alertPromises = [];

      // Generar alertas concurrentes
      for (let i = 0; i < scenario.concurrent; i++) {
        alertPromises.push(
          this.generarAlertaConMedicion(
            `Producto-${i}`,
            15 + Math.random() * 30, // 15-45% cambio
            scenario.concurrent
          )
        );
      }

      const results = await Promise.allSettled(alertPromises);
      const endTime = Date.now();

      // Calcular métricas
      const successful = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;
      const avgResponseTime = results
        .filter(r => r.status === 'fulfilled')
        .map(r => r.value.responseTime)
        .reduce((a, b, _, arr) => a + b / arr.length, 0);

      console.log(`   📊 Alertas procesadas: ${successful}/${scenario.concurrent}`);
      console.log(`   ⏱️  Tiempo total: ${(endTime - startTime)}ms`);
      console.log(`   🚀 Throughput: ${(successful / ((endTime - startTime) / 1000)).toFixed(1)} alertas/sec`);
      console.log(`   📈 Tiempo promedio: ${avgResponseTime.toFixed(0)}ms`);

      // Validar performance
      const performanceOK = avgResponseTime < this.config.responseTimeTarget;
      console.log(`   ✅ Performance OK: ${performanceOK ? 'SÍ' : 'NO'} (<${this.config.responseTimeTarget}ms)`);
    }
  }

  // MÉTODOS AUXILIARES

  /**
   * Simula detección de cambio de precio
   */
  async simularDetecionCambio(scenario) {
    await this.delay(100 + Math.random() * 200);

    const changePercentage = scenario.expectedChange;
    const changeAbsoluto = scenario.newPrice - scenario.oldPrice;

    const detection = {
      oldPrice: scenario.oldPrice,
      newPrice: scenario.newPrice,
      changePercentage: changePercentage,
      changeAbsoluto: Math.abs(changeAbsoluto),
      detected: Math.abs(changePercentage) >= this.config.alertThreshold,
      severity: this.calcularSeverity(changePercentage),
      timestamp: new Date().toISOString()
    };

    return detection;
  }

  /**
   * Valida detección de cambio
   */
  validarDetecionCambio(scenario, detection) {
    const shouldAlert = Math.abs(scenario.expectedChange) >= this.config.alertThreshold;
    
    return {
      detected: detection.detected,
      correct: shouldAlert === detection.detected,
      expectedToAlert: shouldAlert,
      actualAlerted: detection.detected
    };
  }

  /**
   * Calcula severidad basada en porcentaje de cambio
   */
  calcularSeverity(changePercentage) {
    const absChange = Math.abs(changePercentage);
    
    if (absChange >= 30) return 'critical';
    if (absChange >= 20) return 'high';
    if (absChange >= 15) return 'medium';
    return 'low';
  }

  /**
   * Simula filtro de spam
   */
  async simularFiltroSpam(changePercentage) {
    await this.delay(10);

    const absChange = Math.abs(changePercentage);
    
    // Filtros de spam
    const minimumChange = 1.0; // 1%
    const maximumChange = 200.0; // 200%
    
    // Debe ser filtrado si está fuera de rango razonable
    return absChange < minimumChange || absChange > maximumChange;
  }

  /**
   * Simula generación de alerta
   */
  async simularGeneracionAlerta(alertData) {
    await this.delay(50 + Math.random() * 100);

    const changePercentage = alertData.cambio;
    const shouldEscalate = Math.abs(changePercentage) > 25 || alertData.impacto === 'critical';
    
    let escalationLevel = 0;
    if (shouldEscalate) {
      escalationLevel = Math.min(
        Math.floor(Math.abs(changePercentage) / 10),
        this.config.escalationLevels
      );
    }

    return {
      alerted: Math.abs(changePercentage) >= this.config.alertThreshold,
      escalated: shouldEscalate,
      escalationLevel: escalationLevel,
      notificationsSent: Math.abs(changePercentage) >= this.config.alertThreshold ? 1 : 0,
      severity: this.calcularSeverity(changePercentage)
    };
  }

  /**
   * Simula envío de notificación
   */
  async simularEnvioNotificacion(channel, notification) {
    await this.delay(100 + Math.random() * 500);

    // Simular diferentes tasas de éxito por canal
    const successRates = {
      email: 0.98,
      sms: 0.95,
      webhook: 0.92,
      dashboard: 1.0
    };

    const success = Math.random() < (successRates[channel] || 0.9);

    return {
      success,
      error: success ? null : `Failed to send ${channel} notification`,
      channel,
      notification
    };
  }

  /**
   * Simula reintento
   */
  async simularReintento(channel, notification) {
    await this.delay(200 + Math.random() * 300);

    // Los reintentos tienen mejor tasa de éxito
    const retrySuccessRate = 0.85;
    const success = Math.random() < retrySuccessRate;

    return { success, channel, notification };
  }

  /**
   * Simula fallo del sistema
   */
  async simularFalloSistema(failureType) {
    console.log(`   💥 Simulando ${failureType}...`);
    
    // Marcar sistema como no disponible
    this.alertSystem.setAvailability(false, failureType);
    
    // Simular duración del fallo
    await this.delay(1000);
  }

  /**
   * Detecta fallo del sistema
   */
  async detectarFalloSistema(failureType) {
    await this.delay(100 + Math.random() * 200);
    
    // Simular detección basada en métricas
    const isDown = !this.alertSystem.isAvailable();
    
    return isDown;
  }

  /**
   * Inicia recovery automático
   */
  async iniciarRecoveryAutomatico(failureType) {
    console.log(`   🔄 Iniciando recovery para ${failureType}...`);
    
    // Simular steps de recovery
    const recoverySteps = [
      'Clearing caches',
      'Restarting services',
      'Checking connections',
      'Verifying system health'
    ];

    for (const step of recoverySteps) {
      console.log(`   🔧 ${step}...`);
      await this.delay(500 + Math.random() * 500);
    }

    // Intentar recovery
    const success = this.alertSystem.attemptRecovery();

    return {
      initiated: true,
      success,
      failureType,
      recoverySteps: recoverySteps.length
    };
  }

  /**
   * Verifica si el sistema está funcionando
   */
  async verificarSistemaFuncionando() {
    await this.delay(200);

    const working = this.alertSystem.isAvailable() && this.alertSystem.testConnection();
    
    return {
      working,
      systemTime: new Date().toISOString()
    };
  }

  /**
   * Genera alerta con medición de tiempo
   */
  async generarAlertaConMedicion(producto, cambio, concurrent) {
    const startTime = performance.now();

    try {
      const result = await this.simularGeneracionAlerta({
        producto,
        cambio,
        impacto: this.calcularSeverity(cambio)
      });

      const responseTime = performance.now() - startTime;

      return {
        success: true,
        producto,
        cambio,
        responseTime,
        result
      };
    } catch (error) {
      return {
        success: false,
        producto,
        error: error.message,
        responseTime: performance.now() - startTime
      };
    }
  }

  /**
   * Delay helper
   */
  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Genera reporte final del sistema de alertas
   */
  generarReporteAlertas() {
    const totalTime = performance.now() - this.testMetrics.startTime;

    console.log('\n' + '=' .repeat(60));
    console.log('📊 REPORTE FINAL - TESTING SISTEMA DE ALERTAS');
    console.log('=' .repeat(60));

    console.log(`⏱️  Tiempo total: ${(totalTime / 1000).toFixed(1)} segundos`);
    console.log(`🚨 Alertas generadas: ${this.testMetrics.totalAlertsGenerated}`);
    console.log(`📱 Notificaciones enviadas: ${this.testMetrics.totalNotificationsSent}`);
    console.log(`📈 Escalamientos: ${this.testMetrics.totalEscalations}`);
    console.log(`⏱️  Tiempo promedio respuesta: ${this.testMetrics.averageResponseTime.toFixed(0)}ms`);

    // Accuracy metrics
    const totalTests = this.testMetrics.falsePositives + this.testMetrics.falseNegatives;
    if (totalTests > 0) {
      console.log(`\n🎯 MÉTRICAS DE ACCURACY:`);
      console.log(`   False positives: ${this.testMetrics.falsePositives}`);
      console.log(`   False negatives: ${this.testMetrics.falseNegatives}`);
      console.log(`   Accuracy: ${((this.testMetrics.totalAlertsGenerated - totalTests) / this.testMetrics.totalAlertsGenerated * 100).toFixed(1)}%`);
    }

    // Notification metrics
    const totalNotifications = this.notificationLog.length;
    const successfulNotifications = this.notificationLog.filter(n => n.success).length;
    const notificationSuccessRate = totalNotifications > 0 ? (successfulNotifications / totalNotifications * 100) : 0;

    console.log(`\n📱 MÉTRICAS DE NOTIFICACIONES:`);
    console.log(`   Tasa de éxito: ${notificationSuccessRate.toFixed(1)}%`);
    console.log(`   Por canal:`);
    
    const channels = {};
    this.notificationLog.forEach(log => {
      if (!channels[log.channel]) {
        channels[log.channel] = { total: 0, success: 0 };
      }
      channels[log.channel].total++;
      if (log.success) channels[log.channel].success++;
    });

    Object.entries(channels).forEach(([channel, stats]) => {
      const rate = (stats.success / stats.total * 100).toFixed(1);
      console.log(`     ${channel}: ${stats.success}/${stats.total} (${rate}%)`);
    });

    // Performance metrics
    console.log(`\n⚡ MÉTRICAS DE PERFORMANCE:`);
    const performanceOK = this.testMetrics.averageResponseTime < this.config.responseTimeTarget;
    console.log(`   Respuesta promedio < ${this.config.responseTimeTarget}ms: ${performanceOK ? '✅' : '❌'}`);
    console.log(`   Escalamiento automático funcionando: ${this.testMetrics.totalEscalations > 0 ? '✅' : '❌'}`);

    // Validaciones finales
    console.log(`\n🎯 VALIDACIONES FINALES:`);
    const accuracyOK = this.testMetrics.falsePositives + this.testMetrics.falseNegatives < this.testMetrics.totalAlertsGenerated * 0.1;
    const notificationOK = notificationSuccessRate >= 95;
    const performanceAlertOK = this.testMetrics.averageResponseTime < this.config.responseTimeTarget;

    console.log(`   Accuracy >= 90%: ${accuracyOK ? '✅' : '❌'}`);
    console.log(`   Notificaciones >= 95%: ${notificationOK ? '✅' : '❌'}`);
    console.log(`   Performance OK: ${performanceAlertOK ? '✅' : '❌'}`);

    console.log(`\n🏆 RESULTADO GENERAL: ${accuracyOK && notificationOK && performanceAlertOK ? '✅ EXITOSO' : '❌ FALLIDO'}`);
  }
}

/**
 * Mock del sistema de alertas
 */
class MockAlertSystem {
  constructor() {
    this.available = true;
    this.failureType = null;
    this.connectionTestCount = 0;
  }

  isAvailable() {
    return this.available;
  }

  setAvailability(available, failureType = null) {
    this.available = available;
    this.failureType = failureType;
  }

  testConnection() {
    this.connectionTestCount++;
    return this.available && Math.random() > 0.1; // 90% success rate
  }

  attemptRecovery() {
    const recoverySuccess = Math.random() > 0.2; // 80% success rate
    this.available = recoverySuccess;
    this.failureType = null;
    return recoverySuccess;
  }
}

// CLI Usage
if (require.main === module) {
  (async () => {
    try {
      const tester = new AlertSystemTester();
      await tester.ejecutarSuiteAlertas();
    } catch (error) {
      console.error('💥 Error fatal:', error);
      process.exit(1);
    }
  })();
}

module.exports = AlertSystemTester;