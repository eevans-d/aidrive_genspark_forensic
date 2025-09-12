// Dashboard Web Interactivo - JavaScript
// Sistema Inventario Retail Argentino

// Variables globales
let socket;
let demandChartInstance;
let autoRefreshInterval;

// Inicializar dashboard
function initializeDashboard() {
    console.log('🚀 Inicializando Dashboard Interactivo...');

    // Inicializar WebSocket
    initializeWebSocket();

    // Configurar tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    console.log('✅ Dashboard inicializado correctamente');
}

// Inicializar WebSocket para updates tiempo real
function initializeWebSocket() {
    try {
        socket = io();

        socket.on('connect', function() {
            console.log('🔌 WebSocket conectado');
            showNotification('Sistema conectado', 'success');
        });

        socket.on('disconnect', function() {
            console.log('❌ WebSocket desconectado');
            showNotification('Conexión perdida - reintentando...', 'warning');
        });

        socket.on('dashboard_update', function(data) {
            console.log('📊 Actualización dashboard recibida');
            updateDashboardData(data);
        });

    } catch (error) {
        console.warn('⚠️ WebSocket no disponible, usando polling');
        // Fallback a polling cada 30 segundos
        setInterval(refreshDashboard, 30000);
    }
}

// Actualizar datos dashboard
function updateDashboardData(data) {
    try {
        // Actualizar KPIs
        if (data.kpis) {
            updateKPICards(data.kpis);
        }

        // Actualizar alertas badge
        if (data.alertas) {
            document.getElementById('alertasBadge').textContent = data.alertas.criticas || 0;
        }

        // Actualizar timestamp
        if (data.timestamp) {
            updateTimestamp(data.timestamp);
        }

    } catch (error) {
        console.error('Error actualizando dashboard:', error);
    }
}

// Actualizar KPI cards
function updateKPICards(kpis) {
    const kpiMappings = {
        'total_productos': (value) => value.toLocaleString(),
        'disponibilidad': (value) => value.toFixed(1) + '%',
        'valor_inventario': (value) => '$' + value.toLocaleString('es-AR', {minimumFractionDigits: 0}),
        'productos_criticos': (value) => value.toString(),
        'inflacion_diaria': (value) => '$' + value.toLocaleString('es-AR', {minimumFractionDigits: 2})
    };

    Object.keys(kpiMappings).forEach(key => {
        const element = document.querySelector(`[data-kpi="${key}"]`);
        if (element && kpis[key] !== undefined) {
            element.textContent = kpiMappings[key](kpis[key]);
        }
    });
}

// Actualizar timestamp
function updateTimestamp(timestamp) {
    const elements = document.querySelectorAll('[data-timestamp]');
    const formattedTime = new Date(timestamp).toLocaleString('es-AR');
    elements.forEach(el => el.textContent = formattedTime);
}

// Refrescar dashboard completo
function refreshDashboard() {
    console.log('🔄 Actualizando dashboard...');

    showLoadingSpinner(true);

    fetch('/api/dashboard-data')
        .then(response => response.json())
        .then(data => {
            updateDashboardData(data);
            showNotification('Dashboard actualizado', 'success');
        })
        .catch(error => {
            console.error('Error actualizando dashboard:', error);
            showNotification('Error actualizando datos', 'error');
        })
        .finally(() => {
            showLoadingSpinner(false);
        });
}

// Cargar gráfico demanda/predicciones
function loadDemandChart() {
    const ctx = document.getElementById('demandChart');
    if (!ctx) return;

    fetch('/api/charts/demanda?days=30')
        .then(response => response.json())
        .then(data => {
            if (demandChartInstance) {
                demandChartInstance.destroy();
            }

            demandChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [{
                        label: 'Ventas Reales',
                        data: data.ventas_reales,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1,
                        fill: false
                    }, {
                        label: 'Predicciones ML',
                        data: data.predicciones,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderDash: [5, 5],
                        tension: 0.1,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Predicciones vs Realidad - Últimos 30 días'
                        },
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Unidades'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Fecha'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error cargando gráfico demanda:', error);
            ctx.innerHTML = '<div class="text-center text-muted p-4">Error cargando gráfico</div>';
        });
}

// Cargar alertas
function loadAlertas() {
    const container = document.getElementById('alertasContainer');
    if (!container) return;

    container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>';

    fetch('/api/alertas')
        .then(response => response.json())
        .then(data => {
            container.innerHTML = generateAlertasHTML(data);
        })
        .catch(error => {
            console.error('Error cargando alertas:', error);
            container.innerHTML = '<div class="alert alert-danger">Error cargando alertas</div>';
        });
}

// Generar HTML alertas
function generateAlertasHTML(alertas) {
    let html = '';

    // Alertas críticas
    if (alertas.criticas && alertas.criticas.length > 0) {
        html += '<h6 class="text-danger"><i class="fas fa-exclamation-triangle me-2"></i>Críticas</h6>';
        alertas.criticas.forEach(alerta => {
            html += `
                <div class="alert alert-danger d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${alerta.producto}</strong><br>
                        <small>${alerta.mensaje}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="handleAlerta('${alerta.tipo}', '${alerta.producto}')">
                        ${alerta.accion}
                    </button>
                </div>
            `;
        });
    }

    // Advertencias
    if (alertas.advertencias && alertas.advertencias.length > 0) {
        html += '<h6 class="text-warning mt-3"><i class="fas fa-exclamation-circle me-2"></i>Advertencias</h6>';
        alertas.advertencias.forEach(alerta => {
            html += `
                <div class="alert alert-warning d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${alerta.producto}</strong><br>
                        <small>${alerta.mensaje}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-warning" onclick="handleAlerta('${alerta.tipo}', '${alerta.producto}')">
                        ${alerta.accion}
                    </button>
                </div>
            `;
        });
    }

    // Info
    if (alertas.info && alertas.info.length > 0) {
        html += '<h6 class="text-info mt-3"><i class="fas fa-info-circle me-2"></i>Información</h6>';
        alertas.info.forEach(alerta => {
            html += `
                <div class="alert alert-info d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${alerta.producto}</strong><br>
                        <small>${alerta.mensaje}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-info" onclick="handleAlerta('${alerta.tipo}', '${alerta.producto}')">
                        ${alerta.accion}
                    </button>
                </div>
            `;
        });
    }

    return html || '<div class="text-center text-muted p-4">No hay alertas activas</div>';
}

// Manejar acción alerta
function handleAlerta(tipo, producto) {
    console.log(`Manejando alerta ${tipo} para ${producto}`);

    switch(tipo) {
        case 'stock_critico':
        case 'agotado':
            window.location.href = '/compras?producto=' + encodeURIComponent(producto);
            break;
        case 'sobrestockeado':
        case 'sin_movimiento':
            showPromotionModal(producto);
            break;
        default:
            showNotification(`Acción para ${producto} registrada`, 'info');
    }
}

// Configurar búsqueda autocomplete
function setupSearchAutocomplete() {
    const searchInput = document.getElementById('searchProduct');
    if (!searchInput) return;

    let searchTimeout;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            clearSearchResults();
            return;
        }

        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    });

    // Limpiar resultados al perder foco
    searchInput.addEventListener('blur', function() {
        setTimeout(clearSearchResults, 200);
    });
}

// Realizar búsqueda
function performSearch(query) {
    fetch(`/api/productos/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error en búsqueda:', error);
        });
}

// Mostrar resultados búsqueda
function displaySearchResults(productos) {
    const container = document.getElementById('searchResults');
    if (!container) return;

    if (productos.length === 0) {
        container.innerHTML = '<div class="text-muted p-2">No se encontraron productos</div>';
        return;
    }

    let html = '<div class="list-group">';
    productos.forEach(producto => {
        html += `
            <a href="#" class="list-group-item list-group-item-action" onclick="selectProduct('${producto.codigo}')">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${producto.nombre}</h6>
                    <small class="text-success">${producto.precio}</small>
                </div>
                <p class="mb-1">Código: ${producto.codigo}</p>
                <small class="text-muted">Stock: ${producto.stock} unidades</small>
            </a>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

// Limpiar resultados búsqueda
function clearSearchResults() {
    const container = document.getElementById('searchResults');
    if (container) {
        container.innerHTML = '';
    }
}

// Seleccionar producto
function selectProduct(codigo) {
    window.location.href = `/productos?search=${encodeURIComponent(codigo)}`;
}

// Generar reporte diario
function generarReporteDiario() {
    showNotification('Generando reporte diario...', 'info');

    fetch('/api/generar-reporte-diario', {
        method: 'POST'
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `reporte_inventario_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        showNotification('Reporte descargado exitosamente', 'success');
    })
    .catch(error => {
        console.error('Error generando reporte:', error);
        showNotification('Error generando reporte', 'error');
    });
}

// Mostrar modal promoción
function showPromotionModal(producto) {
    const modalHTML = `
        <div class="modal fade" id="promotionModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Promocionar Producto</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>¿Deseas crear una promoción para <strong>${producto}</strong>?</p>
                        <div class="mb-3">
                            <label class="form-label">Descuento (%)</label>
                            <input type="number" class="form-control" id="descuento" value="20" min="5" max="50">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Duración (días)</label>
                            <input type="number" class="form-control" id="duracion" value="7" min="1" max="30">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" onclick="crearPromocion('${producto}')">Crear Promoción</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    const modal = new bootstrap.Modal(document.getElementById('promotionModal'));
    modal.show();
}

// Crear promoción
function crearPromocion(producto) {
    const descuento = document.getElementById('descuento').value;
    const duracion = document.getElementById('duracion').value;

    // Simulación - integrar con backend real
    showNotification(`Promoción ${descuento}% creada para ${producto} por ${duracion} días`, 'success');

    const modal = bootstrap.Modal.getInstance(document.getElementById('promotionModal'));
    modal.hide();
}

// Mostrar loading spinner
function showLoadingSpinner(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

// Mostrar notificaciones toast
function showNotification(message, type = 'info') {
    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'primary'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : type === 'warning' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();

    // Remover elemento después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS'
    }).format(amount);
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('es-AR');
}

function formatDateTime(datetime) {
    return new Date(datetime).toLocaleString('es-AR');
}

// Event listeners globales
document.addEventListener('keydown', function(e) {
    // Ctrl+R o F5 para refresh
    if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
        e.preventDefault();
        refreshDashboard();
    }

    // Ctrl+/ para focus en búsqueda
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        const searchInput = document.getElementById('searchProduct');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

// Cleanup al cerrar página
window.addEventListener('beforeunload', function() {
    if (socket) {
        socket.disconnect();
    }
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});

console.log('✅ Dashboard JavaScript cargado correctamente');