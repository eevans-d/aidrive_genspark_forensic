// Dashboard Web Interactivo - Sistema Inventario Retail Argentino
// JavaScript principal para funcionalidad interactiva

class DashboardInventario {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.lastUpdate = null;
        this.init();
    }

    init() {
        console.log('🚀 Inicializando Dashboard Inventario');
        this.initWebSocket();
        this.initCharts();
        this.initEventListeners();
        this.startPeriodicUpdates();
    }

    // WebSocket Connection
    initWebSocket() {
        try {
            this.socket = io();

            this.socket.on('connect', () => {
                console.log('✅ WebSocket conectado');
                this.updateConnectionStatus(true);
            });

            this.socket.on('disconnect', () => {
                console.log('❌ WebSocket desconectado');
                this.updateConnectionStatus(false);
            });

            this.socket.on('dashboard_update', (data) => {
                console.log('📊 Datos actualizados via WebSocket');
                this.updateDashboard(data);
            });

            this.socket.on('error', (error) => {
                console.error('❌ Error WebSocket:', error);
                this.showNotification('Error de conexión', 'error');
            });
        } catch (error) {
            console.error('❌ Error inicializando WebSocket:', error);
        }
    }

    updateConnectionStatus(isConnected) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            const icon = statusElement.querySelector('i');
            const text = statusElement.querySelector('span');

            if (isConnected) {
                icon.className = 'fas fa-circle';
                icon.style.color = 'var(--success-color)';
                text.textContent = 'Conectado';
            } else {
                icon.className = 'fas fa-circle';
                icon.style.color = 'var(--danger-color)';
                text.textContent = 'Desconectado';
            }
        }
    }

    // Charts Initialization
    initCharts() {
        this.initDemandChart();
        this.initStockChart();
    }

    initDemandChart() {
        const ctx = document.getElementById('demandChart');
        if (!ctx) return;

        this.charts.demand = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Hoy', '+1d', '+2d', '+3d', '+4d', '+5d', '+6d'],
                datasets: [{
                    label: 'Demanda Predicha',
                    data: [85, 92, 78, 105, 118, 95, 102],
                    borderColor: 'var(--primary-color)',
                    backgroundColor: 'rgba(0, 102, 204, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Demanda Real',
                    data: [88, 85, 82, null, null, null, null],
                    borderColor: 'var(--success-color)',
                    backgroundColor: 'transparent',
                    tension: 0.4,
                    borderDash: [5, 5]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Unidades'
                        }
                    }
                }
            }
        });
    }

    initStockChart() {
        const ctx = document.getElementById('stockChart');
        if (!ctx) return;

        this.charts.stock = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Bebidas', 'Alimentos', 'Limpieza', 'Lácteos', 'Otros'],
                datasets: [{
                    data: [35, 28, 15, 12, 10],
                    backgroundColor: [
                        'var(--primary-color)',
                        'var(--success-color)',
                        'var(--warning-color)',
                        'var(--info-color)',
                        'var(--text-secondary)'
                    ],
                    borderWidth: 2,
                    borderColor: 'var(--bg-primary)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }

    // Event Listeners
    initEventListeners() {
        // Chart period selector
        const chartPeriod = document.getElementById('chartPeriod');
        if (chartPeriod) {
            chartPeriod.addEventListener('change', (e) => {
                this.updateChartPeriod(e.target.value);
            });
        }

        // Mobile menu toggle
        const mobileToggle = document.getElementById('mobileMenuToggle');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', this.toggleMobileMenu);
        }

        // Notification badge click
        const notificationIcon = document.querySelector('.notification-icon');
        if (notificationIcon) {
            notificationIcon.addEventListener('click', this.showNotifications);
        }
    }

    // Dashboard Updates
    updateDashboard(data) {
        this.updateKPIs(data.kpis);
        this.updateAlerts(data.alertas_criticas);
        this.updateRecommendations(data.recomendaciones_compra);
        this.updateLastUpdateTime();
    }

    updateKPIs(kpis) {
        if (!kpis) return;

        const updates = [
            { id: 'productosStock', value: kpis.productos_stock },
            { id: 'valorInventario', value: kpis.valor_inventario },
            { id: 'disponibilidad', value: kpis.disponibilidad },
            { id: 'coberturaDias', value: kpis.cobertura_dias + ' días' }
        ];

        updates.forEach(({ id, value }) => {
            const element = document.getElementById(id);
            if (element && element.textContent !== value) {
                element.textContent = value;
                element.classList.add('fade-in');
                setTimeout(() => element.classList.remove('fade-in'), 500);
            }
        });
    }

    updateAlerts(alerts) {
        if (!alerts) return;

        const container = document.getElementById('alertsContainer');
        const badge = document.getElementById('alertsCount');

        if (badge) {
            badge.textContent = alerts.length;
        }

        // Actualizar contador de notificaciones
        const notificationBadge = document.getElementById('notificationBadge');
        if (notificationBadge) {
            notificationBadge.textContent = alerts.filter(a => a.urgencia === 'crítica').length;
        }
    }

    updateRecommendations(recommendations) {
        if (!recommendations) return;
        // Las recomendaciones se actualizan via server-side rendering
        console.log('📋 Recomendaciones actualizadas:', recommendations.length);
    }

    updateLastUpdateTime() {
        const element = document.getElementById('lastUpdate');
        if (element) {
            const now = new Date();
            element.textContent = now.toLocaleString('es-AR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }

    // Chart Updates
    updateChartPeriod(period) {
        console.log('📊 Actualizando período del gráfico:', period);

        let labels, data;
        switch(period) {
            case '7':
                labels = ['Hoy', '+1d', '+2d', '+3d', '+4d', '+5d', '+6d'];
                data = [85, 92, 78, 105, 118, 95, 102];
                break;
            case '15':
                labels = Array.from({length: 15}, (_, i) => `+${i}d`);
                data = Array.from({length: 15}, () => Math.floor(Math.random() * 50) + 80);
                break;
            case '30':
                labels = Array.from({length: 30}, (_, i) => `+${i}d`);
                data = Array.from({length: 30}, () => Math.floor(Math.random() * 60) + 70);
                break;
        }

        if (this.charts.demand) {
            this.charts.demand.data.labels = labels;
            this.charts.demand.data.datasets[0].data = data;
            this.charts.demand.update();
        }
    }

    // Periodic Updates
    startPeriodicUpdates() {
        // Actualizar cada 30 segundos
        setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('request_update');
            }
        }, 30000);

        // Actualizar timestamp cada segundo
        setInterval(() => {
            this.updateLastUpdateTime();
        }, 1000);
    }

    // Utility Functions
    toggleMobileMenu() {
        const navMenu = document.querySelector('.nav-menu');
        if (navMenu) {
            navMenu.classList.toggle('mobile-active');
        }
    }

    showNotifications() {
        console.log('🔔 Mostrando notificaciones');
        // Implementar dropdown de notificaciones
        this.showNotification('Ver todas las alertas críticas', 'info');
    }

    showNotification(message, type = 'info') {
        // Crear notification toast
        const notification = document.createElement('div');
        notification.className = `notification toast-${type}`;
        notification.textContent = message;

        // Estilos inline básicos
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '1rem 1.5rem',
            backgroundColor: type === 'error' ? 'var(--danger-color)' : 'var(--primary-color)',
            color: 'white',
            borderRadius: 'var(--border-radius)',
            zIndex: '3000',
            opacity: '0',
            transform: 'translateX(100%)',
            transition: 'all 0.3s ease'
        });

        document.body.appendChild(notification);

        // Animación de entrada
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Auto-remove después de 3 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Purchase Management Functions
function quickOrder(producto) {
    console.log('🛒 Pedido rápido:', producto);
    dashboard.showNotification(`Iniciando pedido para ${producto}`, 'info');

    // Simular proceso de pedido
    setTimeout(() => {
        dashboard.showNotification(`Pedido de ${producto} enviado al proveedor`, 'success');
    }, 2000);
}

function viewProduct(producto) {
    console.log('👁️ Ver producto:', producto);
    // Redirigir a página de productos con filtro
    window.location.href = `/productos?search=${encodeURIComponent(producto)}`;
}

function confirmPurchase(producto, cantidad, costo) {
    console.log('✅ Confirmar compra:', { producto, cantidad, costo });

    const modal = document.getElementById('purchaseModal');
    const modalBody = document.getElementById('purchaseModalBody');

    if (modal && modalBody) {
        modalBody.innerHTML = `
            <div class="purchase-confirmation">
                <h4>Confirmar Compra</h4>
                <div class="purchase-details">
                    <p><strong>Producto:</strong> ${producto}</p>
                    <p><strong>Cantidad:</strong> ${cantidad} unidades</p>
                    <p><strong>Costo Total:</strong> $${costo.toLocaleString('es-AR')}</p>
                </div>
                <div class="purchase-notes">
                    <label for="purchaseNotes">Notas adicionales:</label>
                    <textarea id="purchaseNotes" class="form-control" rows="3" 
                              placeholder="Agregar instrucciones para el proveedor..."></textarea>
                </div>
            </div>
        `;

        modal.style.display = 'block';

        // Store purchase data for execution
        modal.dataset.producto = producto;
        modal.dataset.cantidad = cantidad;
        modal.dataset.costo = costo;
    }
}

function closePurchaseModal() {
    const modal = document.getElementById('purchaseModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function executePurchase() {
    const modal = document.getElementById('purchaseModal');
    const notes = document.getElementById('purchaseNotes')?.value || '';

    if (modal) {
        const producto = modal.dataset.producto;
        const cantidad = modal.dataset.cantidad;
        const costo = modal.dataset.costo;

        console.log('💰 Ejecutando compra:', { producto, cantidad, costo, notes });

        // Simular envío al sistema
        dashboard.showNotification('Procesando compra...', 'info');

        setTimeout(() => {
            dashboard.showNotification(`Compra de ${producto} registrada exitosamente`, 'success');
            closePurchaseModal();
        }, 1500);
    }
}

function generatePurchaseList() {
    console.log('📋 Generando lista de compras');
    dashboard.showNotification('Generando lista de compras...', 'info');

    // Simular generación
    setTimeout(() => {
        const blob = new Blob([
            'LISTA DE COMPRAS - ' + new Date().toLocaleDateString('es-AR') + '\n\n' +
            '1. Coca Cola 2L - 24 unidades - $28,800\n' +
            '2. Arroz 1kg - 50 unidades - $15,000\n' +
            '3. Yerba Mate 1kg - 15 unidades - $9,750\n\n' +
            'TOTAL: $53,550'
        ], { type: 'text/plain' });

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `lista_compras_${new Date().toLocaleDateString('es-AR').replace(/\//g, '-')}.txt`;
        a.click();
        window.URL.revokeObjectURL(url);

        dashboard.showNotification('Lista de compras descargada', 'success');
    }, 1000);
}

// Initialize Dashboard
let dashboard;

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 DOM cargado, inicializando dashboard');
    dashboard = new DashboardInventario();
});

// Handle modal clicks outside content
document.addEventListener('click', function(e) {
    const modal = document.getElementById('purchaseModal');
    if (e.target === modal) {
        closePurchaseModal();
    }
});

// Export for global access
window.dashboard = dashboard;
window.quickOrder = quickOrder;
window.viewProduct = viewProduct;
window.confirmPurchase = confirmPurchase;
window.closePurchaseModal = closePurchaseModal;
window.executePurchase = executePurchase;
window.generatePurchaseList = generatePurchaseList;
