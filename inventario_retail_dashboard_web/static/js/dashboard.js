/**
 * Dashboard JavaScript - Sistema Inventario Retail Argentino
 * Funcionalidades interactivas, WebSockets, actualizaciones tiempo real
 */

// Variables globales
let socket = null;
let dashboardData = {};
let refreshInterval = null;

// Inicializar dashboard
function initializeDashboard() {
    console.log('Inicializando dashboard...');

    // Cargar datos iniciales
    loadDashboardData();

    // Configurar event listeners
    setupEventListeners();

    // Inicializar tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    console.log('Dashboard inicializado correctamente');
}

// Configurar WebSocket
function initializeWebSocket() {
    try {
        socket = io();

        socket.on('connect', function() {
            console.log('WebSocket conectado');
            updateConnectionStatus(true);
        });

        socket.on('disconnect', function() {
            console.log('WebSocket desconectado');
            updateConnectionStatus(false);
        });

        socket.on('dashboard_update', function(data) {
            console.log('Actualización dashboard recibida');
            updateDashboardData(data);
        });

        socket.on('factura_procesada', function(data) {
            console.log('Factura procesada:', data.filename);
            showNotification('success', `Factura ${data.filename} procesada correctamente`);
        });

        // Solicitar actualización cada 30 segundos
        setInterval(() => {
            if (socket && socket.connected) {
                socket.emit('request_dashboard_update');
            }
        }, 30000);

    } catch(error) {
        console.error('Error inicializando WebSocket:', error);
        updateConnectionStatus(false);
    }
}

// Cargar datos dashboard
async function loadDashboardData() {
    try {
        showLoading(true);

        const response = await axios.get('/api/dashboard-data');

        if (response.data) {
            dashboardData = response.data;
            updateDashboardDisplay(response.data);
        }

    } catch(error) {
        console.error('Error cargando datos dashboard:', error);
        showNotification('error', 'Error cargando datos del dashboard');
    } finally {
        showLoading(false);
    }
}

// Actualizar display dashboard
function updateDashboardDisplay(data) {
    // Actualizar timestamp
    const timestampEl = document.getElementById('last-update');
    if (timestampEl && data.timestamp) {
        const date = new Date(data.timestamp);
        timestampEl.textContent = date.toLocaleString('es-AR');
    }

    // Actualizar KPIs
    updateKPIs(data.kpis || {});

    // Actualizar alertas
    updateAlerts(data.alertas || []);

    // Actualizar compras urgentes
    updateComprasUrgentes(data.compras_urgentes || []);

    console.log('Dashboard actualizado');
}

// Actualizar KPIs
function updateKPIs(kpis) {
    const kpiElements = {
        'kpi-disponibilidad': kpis.disponibilidad_productos || '0%',
        'kpi-inversion': formatCurrency(kpis.inversion_total || 0),
        'kpi-cobertura': `${kpis.cobertura_dias || 0} días`,
        'kpi-inflacion': formatCurrency(kpis.impacto_inflacion_diario || 0)
    };

    Object.entries(kpiElements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            // Animación cambio valor
            element.style.transform = 'scale(1.1)';
            element.textContent = value;

            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 200);
        }
    });
}

// Actualizar alertas
function updateAlerts(alertas) {
    const container = document.getElementById('alertas-container');
    const countEl = document.getElementById('alertas-count');

    if (!container) return;

    // Actualizar contador
    if (countEl) {
        countEl.textContent = alertas.length;
    }

    if (alertas.length === 0) {
        container.innerHTML = `
            <div class="alert alert-success mb-0">
                <i class="fas fa-check-circle"></i>
                No hay alertas críticas en este momento
            </div>
        `;
        return;
    }

    // Generar HTML alertas
    const alertasHTML = alertas.map(alerta => `
        <div class="alert alert-${alerta.prioridad === 'CRITICA' ? 'danger' : 'warning'} mb-2">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>${alerta.producto}</strong><br>
                    <small>${alerta.mensaje}</small>
                </div>
                <span class="badge bg-${alerta.prioridad === 'CRITICA' ? 'danger' : 'warning'}">
                    ${alerta.prioridad}
                </span>
            </div>
        </div>
    `).join('');

    container.innerHTML = alertasHTML;
}

// Actualizar compras urgentes
function updateComprasUrgentes(compras) {
    const container = document.getElementById('compras-container');
    const countEl = document.getElementById('compras-count');

    if (!container) return;

    // Actualizar contador
    if (countEl) {
        countEl.textContent = compras.length;
    }

    if (compras.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info mb-0">
                <i class="fas fa-info-circle"></i>
                No hay compras urgentes recomendadas para hoy
            </div>
        `;
        return;
    }

    // Calcular total
    const total = compras.reduce((sum, compra) => sum + (compra.costo_total || 0), 0);

    // Generar HTML compras
    const comprasHTML = compras.map(compra => `
        <div class="compra-item ${compra.urgencia === 'CRITICA' ? 'compra-urgente' : ''}">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${compra.producto}</strong><br>
                    <small class="text-muted">
                        Cantidad: ${compra.cantidad} unidades
                    </small>
                </div>
                <div class="text-end">
                    <div class="h6 text-success mb-0">${formatCurrency(compra.costo_total)}</div>
                    <small class="text-muted">${compra.motivo}</small>
                </div>
            </div>
        </div>
    `).join('');

    const totalHTML = `
        <div class="mt-3 p-3 bg-light rounded">
            <div class="d-flex justify-content-between">
                <strong>Total Inversión HOY:</strong>
                <strong class="text-success" id="total-inversion">
                    ${formatCurrency(total)}
                </strong>
            </div>
        </div>
    `;

    container.innerHTML = comprasHTML + totalHTML;
}

// Refresh dashboard manual
async function refreshDashboard() {
    const refreshIcon = document.getElementById('refresh-icon');

    if (refreshIcon) {
        refreshIcon.classList.add('fa-spin');
    }

    try {
        await loadDashboardData();
        showNotification('success', 'Dashboard actualizado correctamente');
    } catch(error) {
        showNotification('error', 'Error actualizando dashboard');
    } finally {
        if (refreshIcon) {
            refreshIcon.classList.remove('fa-spin');
        }
    }
}

// Configurar event listeners
function setupEventListeners() {
    // Refresh manual
    const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }

    // Escape key para refresh
    document.addEventListener('keydown', function(e) {
        if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
            e.preventDefault();
            refreshDashboard();
        }
    });

    // Click en alertas para expandir
    document.addEventListener('click', function(e) {
        if (e.target.closest('.alert')) {
            const alert = e.target.closest('.alert');
            alert.classList.toggle('expanded');
        }
    });
}

// Actualizar estado conexión
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');

    if (statusEl) {
        statusEl.className = `status-indicator ${connected ? 'status-ok' : 'status-critical'}`;
    }

    // Mostrar notificación si se desconecta
    if (!connected) {
        showNotification('warning', 'Conexión perdida. Reintentando...');
    }
}

// Mostrar loading
function showLoading(show) {
    const existingLoader = document.getElementById('dashboard-loader');

    if (show && !existingLoader) {
        const loader = document.createElement('div');
        loader.id = 'dashboard-loader';
        loader.className = 'position-fixed top-50 start-50 translate-middle';
        loader.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        `;
        document.body.appendChild(loader);
    } else if (!show && existingLoader) {
        existingLoader.remove();
    }
}

// Mostrar notificaciones
function showNotification(type, message) {
    // Crear toast notification
    const toastContainer = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'warning'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'exclamation-triangle'}"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Auto remove after hide
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Crear container para toasts
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Formatear moneda argentina
function formatCurrency(amount) {
    if (typeof amount !== 'number') {
        amount = parseFloat(amount) || 0;
    }

    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS'
    }).format(amount);
}

// Formatear números
function formatNumber(number) {
    if (typeof number !== 'number') {
        number = parseFloat(number) || 0;
    }

    return new Intl.NumberFormat('es-AR').format(number);
}

// Exportar funciones globales
window.initializeDashboard = initializeDashboard;
window.initializeWebSocket = initializeWebSocket;
window.refreshDashboard = refreshDashboard;
window.showNotification = showNotification;
window.formatCurrency = formatCurrency;

console.log('Dashboard JS cargado correctamente');