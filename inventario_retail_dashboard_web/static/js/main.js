/**
 * Main JavaScript - Sistema Inventario Retail Argentino
 * Funciones globales y utilities
 */

// Configuración global
const CONFIG = {
    API_BASE_URL: '',
    REFRESH_INTERVAL: 30000, // 30 segundos
    CURRENCY: 'ARS',
    LOCALE: 'es-AR',
    TIMEZONE: 'America/Argentina/Buenos_Aires'
};

// Utilities globales
const Utils = {

    // Formatear fecha argentina
    formatDate(date, options = {}) {
        const defaultOptions = {
            timeZone: CONFIG.TIMEZONE,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            ...options
        };

        return new Date(date).toLocaleDateString(CONFIG.LOCALE, defaultOptions);
    },

    // Formatear hora argentina
    formatTime(date) {
        return new Date(date).toLocaleTimeString(CONFIG.LOCALE, {
            timeZone: CONFIG.TIMEZONE,
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Formatear moneda
    formatCurrency(amount) {
        return new Intl.NumberFormat(CONFIG.LOCALE, {
            style: 'currency',
            currency: CONFIG.CURRENCY
        }).format(amount || 0);
    },

    // Debounce función
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Throttle función
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Validar CUIT argentino
    validateCUIT(cuit) {
        if (!cuit || typeof cuit !== 'string') return false;

        // Remover guiones y espacios
        cuit = cuit.replace(/[-\s]/g, '');

        if (cuit.length !== 11) return false;

        // Verificar que sean solo números
        if (!/^\d+$/.test(cuit)) return false;

        // Algoritmo verificación dígito
        const digits = cuit.split('').map(Number);
        const multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2];

        let sum = 0;
        for (let i = 0; i < 10; i++) {
            sum += digits[i] * multipliers[i];
        }

        const remainder = sum % 11;
        const checkDigit = remainder < 2 ? remainder : 11 - remainder;

        return checkDigit === digits[10];
    },

    // Generar ID único
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    // Copiar al clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback para navegadores que no soportan clipboard API
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                return true;
            } catch (fallbackErr) {
                return false;
            } finally {
                document.body.removeChild(textArea);
            }
        }
    }
};

// API Helper
const API = {

    // GET request
    async get(endpoint, params = {}) {
        try {
            const url = new URL(CONFIG.API_BASE_URL + endpoint, window.location.origin);
            Object.keys(params).forEach(key => {
                if (params[key] !== null && params[key] !== undefined) {
                    url.searchParams.append(key, params[key]);
                }
            });

            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API GET error:', error);
            throw error;
        }
    },

    // POST request
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(CONFIG.API_BASE_URL + endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API POST error:', error);
            throw error;
        }
    },

    // Upload file
    async upload(endpoint, formData) {
        try {
            const response = await fetch(CONFIG.API_BASE_URL + endpoint, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Upload error:', error);
            throw error;
        }
    }
};

// Storage Helper
const Storage = {

    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Storage set error:', error);
        }
    },

    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    },

    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Storage remove error:', error);
        }
    },

    clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Storage clear error:', error);
        }
    }
};

// Inicialización global
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema Inventario Retail Argentino inicializado');

    // Configurar timezone
    if (Intl.DateTimeFormat().resolvedOptions().timeZone !== CONFIG.TIMEZONE) {
        console.log(`Timezone detectado: ${Intl.DateTimeFormat().resolvedOptions().timeZone}`);
        console.log(`Usando timezone configurado: ${CONFIG.TIMEZONE}`);
    }

    // Detectar si es mobile
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
        document.body.classList.add('mobile-device');
    }

    // Configurar service worker si está disponible
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('Service Worker registrado:', registration);
            })
            .catch(error => {
                console.log('Error registrando Service Worker:', error);
            });
    }
});

// Exportar globalmente
window.Utils = Utils;
window.API = API;
window.Storage = Storage;
window.CONFIG = CONFIG;

console.log('Main JS cargado correctamente');