/**
 * Charts JavaScript - Gráficos interactivos Dashboard
 * Chart.js configuración para predicciones y métricas
 */

// Variables gráficos
let demandChart = null;
let stockChart = null;

// Configuración colores argentinos
const COLORS = {
    primary: '#0d6efd',
    success: '#198754', 
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#0dcaf0',
    argentina: {
        celeste: '#74ACDF',
        blanco: '#FFFFFF',
        sol: '#F9A602'
    }
};

// Inicializar todos los gráficos
function loadCharts() {
    console.log('Inicializando gráficos...');

    try {
        initDemandChart();
        initStockChart();

        console.log('Gráficos inicializados correctamente');
    } catch(error) {
        console.error('Error inicializando gráficos:', error);
    }
}

// Gráfico predicciones demanda
function initDemandChart() {
    const ctx = document.getElementById('demandChart');
    if (!ctx) return;

    // Datos ejemplo (se actualizarán con datos reales)
    const labels = [];
    const today = new Date();

    for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        labels.push(date.toLocaleDateString('es-AR', { 
            weekday: 'short', 
            day: 'numeric' 
        }));
    }

    const data = {
        labels: labels,
        datasets: [
            {
                label: 'Demanda Predicha',
                data: [120, 135, 98, 145, 160, 125, 110],
                borderColor: COLORS.primary,
                backgroundColor: COLORS.primary + '20',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Stock Actual',
                data: [100, 85, 95, 80, 65, 55, 45],
                borderColor: COLORS.warning,
                backgroundColor: COLORS.warning + '20',
                tension: 0.4,
                fill: false
            },
            {
                label: 'Punto Reorden',
                data: [50, 50, 50, 50, 50, 50, 50],
                borderColor: COLORS.danger,
                backgroundColor: COLORS.danger + '10',
                borderDash: [5, 5],
                fill: false
            }
        ]
    };

    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} unidades`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#e0e0e0'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + ' un.';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    };

    demandChart = new Chart(ctx, config);
}

// Gráfico estado stock
function initStockChart() {
    const ctx = document.getElementById('stockChart');
    if (!ctx) return;

    const data = {
        labels: [
            'Stock Normal',
            'Stock Bajo', 
            'Stock Crítico',
            'Sobrestockeado'
        ],
        datasets: [{
            data: [65, 20, 10, 5],
            backgroundColor: [
                COLORS.success,
                COLORS.warning,
                COLORS.danger,
                COLORS.info
            ],
            borderWidth: 2,
            borderColor: '#ffffff'
        }]
    };

    const config = {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed * 100) / total).toFixed(1);
                            return `${context.label}: ${context.parsed} productos (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    };

    stockChart = new Chart(ctx, config);
}

// Actualizar gráfico demanda con datos reales
function updateDemandChart(predictionsData) {
    if (!demandChart || !predictionsData) return;

    try {
        // Actualizar labels (fechas)
        const labels = predictionsData.fechas || demandChart.data.labels;

        // Actualizar datasets
        if (predictionsData.demanda_predicha) {
            demandChart.data.datasets[0].data = predictionsData.demanda_predicha;
        }

        if (predictionsData.stock_actual) {
            demandChart.data.datasets[1].data = predictionsData.stock_actual;
        }

        if (predictionsData.punto_reorden) {
            demandChart.data.datasets[2].data = predictionsData.punto_reorden;
        }

        demandChart.data.labels = labels;
        demandChart.update('active');

        console.log('Gráfico demanda actualizado');
    } catch(error) {
        console.error('Error actualizando gráfico demanda:', error);
    }
}

// Actualizar gráfico stock con datos reales
function updateStockChart(stockData) {
    if (!stockChart || !stockData) return;

    try {
        const data = [
            stockData.normal || 0,
            stockData.bajo || 0,
            stockData.critico || 0,
            stockData.sobrestockeado || 0
        ];

        stockChart.data.datasets[0].data = data;
        stockChart.update('active');

        console.log('Gráfico stock actualizado');
    } catch(error) {
        console.error('Error actualizando gráfico stock:', error);
    }
}

// Crear gráfico mini para widgets
function createMiniChart(canvasId, data, type = 'line') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const config = {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false
                }
            },
            elements: {
                point: {
                    radius: 0
                }
            }
        }
    };

    return new Chart(ctx, config);
}

// Destruir gráficos (cleanup)
function destroyCharts() {
    if (demandChart) {
        demandChart.destroy();
        demandChart = null;
    }

    if (stockChart) {
        stockChart.destroy();
        stockChart = null;
    }
}

// Redimensionar gráficos
function resizeCharts() {
    if (demandChart) {
        demandChart.resize();
    }

    if (stockChart) {
        stockChart.resize();
    }
}

// Event listeners
window.addEventListener('resize', resizeCharts);

// Exportar funciones
window.loadCharts = loadCharts;
window.updateDemandChart = updateDemandChart;
window.updateStockChart = updateStockChart;
window.createMiniChart = createMiniChart;
window.destroyCharts = destroyCharts;

console.log('Charts JS cargado correctamente');