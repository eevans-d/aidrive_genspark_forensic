# SEMANA 2.3 - Instrucciones Frontend Integration

**Estado:** 🔄 PRÓXIMA FASE  
**Objetivos:** Integrar WebSocket con UI, Toast Notifications, Bell Icon, Notification Center  
**Tiempo Estimado:** 3-3.5 horas  
**Tests Planeados:** 15-20 tests adicionales  
**Commit:** Por crear  

---

## 🎯 Objetivo General

Integrar el WebSocket backend (completado en SEMANA 2.2) con la interfaz de usuario del dashboard, proporcionando notificaciones en tiempo real visibles, toast notifications, y un centro de notificaciones completo.

---

## 📋 Tareas Principales

### 1. Integración de WebSocket JavaScript Manager

**Archivo:** inventario-retail/web_dashboard/static/js/websocket-notifications.js (YA EXISTE desde SEMANA 2.1)

**Status:** Código cliente YA IMPLEMENTADO, necesita conexión al endpoint

**Tareas:**

```
✓ 1.1 Validar que websocket-notifications.js existe y es completo
✓ 1.2 Incluir en base.html template
✓ 1.3 Inicializar con parámetros correctos (user_id, api_key)
✓ 1.4 Conectar a /ws/notifications endpoint
✓ 1.5 Testing de conexión exitosa
```

**Código de inicialización a agregar en base.html:**

```html
<!-- En antes del cierre de </body> -->
<script>
  // Obtener user_id del DOM (debe estar en context)
  const userId = {{ current_user_id }};
  const apiKey = "{{ api_key }}";
  
  // Inicializar WebSocket Notification Manager
  const notificationManager = new WebSocketNotificationManager({
    wsUrl: `ws://${window.location.host}/ws/notifications`,
    userId: userId,
    apiKey: apiKey,
    onConnect: () => {
      console.log('✅ Connected to notification server');
      // Opcional: mostrar indicator de conexión
    },
    onDisconnect: () => {
      console.warn('⚠️ Disconnected from notification server');
      // Opcional: mostrar indicator de desconexión
    },
    onNotification: (notification) => {
      console.log('📬 New notification:', notification);
      // Este handler ya muestra toast en websocket-notifications.js
    },
    onError: (error) => {
      console.error('❌ Notification error:', error);
    }
  });
  
  // Conectar
  notificationManager.connect();
  
  // Guardar en window para acceso desde otras scripts
  window.notificationManager = notificationManager;
</script>
```

**Validaciones:**

- [ ] WebSocket conecta sin errores
- [ ] Recibe "connection_established" message
- [ ] Recibe "unread_count" inicial
- [ ] Toast aparece cuando llega notificación
- [ ] Counter en bell icon se actualiza

---

### 2. Toast Notifications en HTML/CSS

**Responsabilidad:** Ya está en websocket-notifications.js, pero necesita CSS en main template

**Código CSS a agregar en static/css/main.css:**

```css
/* Notification Toast Container */
#notification-toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    max-width: 400px;
    pointer-events: none;
}

/* Individual Toast */
.notification-toast {
    background: white;
    border-left: 4px solid #2563eb;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    padding: 16px;
    margin-bottom: 12px;
    pointer-events: auto;
    animation: slideInRight 0.3s ease-out;
}

.notification-toast.error {
    border-left-color: #ef4444;
}

.notification-toast.warning {
    border-left-color: #f59e0b;
}

.notification-toast.success {
    border-left-color: #10b981;
}

.notification-toast.critical {
    border-left-color: #8b5cf6;
    background: #f8f0ff;
}

.notification-toast-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.notification-toast-subject {
    font-weight: 600;
    font-size: 14px;
    color: #1f2937;
}

.notification-toast-timestamp {
    font-size: 12px;
    color: #6b7280;
}

.notification-toast-close {
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    font-size: 18px;
    padding: 0;
}

.notification-toast-close:hover {
    color: #4b5563;
}

.notification-toast-message {
    font-size: 14px;
    color: #4b5563;
    line-height: 1.5;
}

@keyframes slideInRight {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(400px);
        opacity: 0;
    }
}

/* Mobile responsive */
@media (max-width: 640px) {
    #notification-toast-container {
        top: auto;
        bottom: 10px;
        left: 10px;
        right: 10px;
        max-width: none;
    }
    
    .notification-toast {
        margin-bottom: 8px;
    }
}
```

**Tareas:**

```
✓ 2.1 Agregar CSS a main.css
✓ 2.2 Testing visual de toasts
✓ 2.3 Testing en mobile
✓ 2.4 Testing de auto-dismiss (5s)
✓ 2.5 Testing de colores por prioridad
```

---

### 3. Bell Icon + Notification Counter

**Ubicación:** Navbar/Header del dashboard  

**HTML a agregar en base.html:**

```html
<!-- En navbar, agregar notification bell -->
<div style="display: flex; align-items: center; gap: 15px;">
    <div id="notification-bell" style="
        position: relative;
        cursor: pointer;
        font-size: 24px;
        display: inline-block;
        transition: all 0.2s ease;
    " title="Notifications">
        🔔
        <span id="notification-counter" style="
            position: absolute;
            top: -8px;
            right: -8px;
            background: #ef4444;
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            visibility: hidden;
        ">0</span>
    </div>
</div>
```

**JavaScript Logic ya en websocket-notifications.js:**

```javascript
// El counter se actualiza automáticamente via:
// 1. WebSocket message type "unread_count"
// 2. localStorage backup
// 3. Visual update + animation

// Métodos disponibles:
notificationManager.incrementUnreadCount()
notificationManager.updateUnreadCount(count)
notificationManager.loadUnreadCount()
```

**Tareas:**

```
✓ 3.1 Agregar HTML del bell icon
✓ 3.2 Posicionar en navbar correctamente
✓ 3.3 Verificar counter se actualiza via WebSocket
✓ 3.4 Testing de click (próximo: notification center)
✓ 3.5 Testing de animación
✓ 3.6 Testing en mobile
```

---

### 4. Notification Center Modal

**Archivo Nuevo:** inventario-retail/web_dashboard/templates/notification_center_modal.html

**Funcionalidad:**
- Mostrar lista de todas las notificaciones
- Paginación (10 por página)
- Marcar como leída
- Filtros (leídas/no leídas)
- Buscar por texto

**HTML Structure:**

```html
<!-- Notification Center Modal -->
<div id="notification-center-modal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 10000;">
    <div style="background: white; border-radius: 8px; max-width: 600px; max-height: 80vh; overflow-y: auto; margin: auto; margin-top: 10vh;">
        
        <!-- Header -->
        <div style="padding: 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin: 0; font-size: 18px; font-weight: 600;">Notificaciones</h2>
            <button style="background: none; border: none; font-size: 24px; cursor: pointer;" onclick="closeNotificationCenter()">&times;</button>
        </div>
        
        <!-- Filters -->
        <div style="padding: 12px 20px; border-bottom: 1px solid #e5e7eb; display: flex; gap: 10px;">
            <button onclick="filterNotifications('all')" class="notification-filter-btn active">Todas</button>
            <button onclick="filterNotifications('unread')" class="notification-filter-btn">No leídas</button>
            <button onclick="filterNotifications('read')" class="notification-filter-btn">Leídas</button>
        </div>
        
        <!-- Notifications List -->
        <div id="notification-center-list" style="padding: 0;">
            <!-- Loaded dynamically -->
        </div>
        
        <!-- Pagination -->
        <div id="notification-center-pagination" style="padding: 12px 20px; text-align: center; border-top: 1px solid #e5e7eb;">
            <!-- Loaded dynamically -->
        </div>
        
    </div>
</div>

<style>
.notification-item {
    padding: 16px 20px;
    border-bottom: 1px solid #f3f4f6;
    display: flex;
    gap: 12px;
    cursor: pointer;
    transition: background 0.2s;
}

.notification-item:hover {
    background: #f9fafb;
}

.notification-item.unread {
    background: #f0f9ff;
}

.notification-item-content {
    flex: 1;
}

.notification-item-subject {
    font-weight: 600;
    color: #1f2937;
}

.notification-item-message {
    font-size: 14px;
    color: #6b7280;
    margin-top: 4px;
}

.notification-item-timestamp {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 6px;
}

.notification-item-badge {
    width: 12px;
    height: 12px;
    background: #2563eb;
    border-radius: 50%;
    align-self: center;
    margin-right: 8px;
}

.notification-filter-btn {
    padding: 6px 12px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
}

.notification-filter-btn.active {
    background: #2563eb;
    color: white;
    border-color: #2563eb;
}
</style>
```

**JavaScript Controller:**

```javascript
// En static/js/notification-center.js
class NotificationCenterModal {
    constructor(notificationManager) {
        this.manager = notificationManager;
        this.currentFilter = 'all';
        this.currentPage = 0;
        this.pageSize = 10;
        this.notifications = [];
    }
    
    async load() {
        // Cargar notificaciones desde API REST
        // GET /api/notifications?user_id={id}&limit=100&offset=0
        
        const response = await fetch(
            `/api/notifications?user_id=${this.manager.userId}&limit=100&offset=0`,
            {headers: {'X-API-Key': this.manager.apiKey}}
        );
        
        const data = await response.json();
        this.notifications = data.notifications;
        this.render();
    }
    
    render() {
        // Filtrar
        let filtered = this.notifications;
        if (this.currentFilter === 'unread') {
            filtered = filtered.filter(n => !n.read);
        } else if (this.currentFilter === 'read') {
            filtered = filtered.filter(n => n.read);
        }
        
        // Paginar
        const start = this.currentPage * this.pageSize;
        const page = filtered.slice(start, start + this.pageSize);
        
        // Renderizar
        const html = page.map(n => this.renderNotification(n)).join('');
        document.getElementById('notification-center-list').innerHTML = html;
        
        // Pagination buttons
        const totalPages = Math.ceil(filtered.length / this.pageSize);
        this.renderPagination(totalPages);
    }
    
    async markAsRead(notificationId) {
        await fetch(
            `/api/notifications/${notificationId}/read`,
            {
                method: 'POST',
                headers: {'X-API-Key': this.manager.apiKey}
            }
        );
        
        await this.load();
    }
    
    show() {
        document.getElementById('notification-center-modal').style.display = 'flex';
        this.load();
    }
    
    close() {
        document.getElementById('notification-center-modal').style.display = 'none';
    }
}

// Global instance
let notificationCenter = null;

// Attach to bell icon
document.getElementById('notification-bell').addEventListener('click', () => {
    if (!notificationCenter) {
        notificationCenter = new NotificationCenterModal(window.notificationManager);
    }
    notificationCenter.show();
});
```

**Tareas:**

```
✓ 4.1 Crear HTML del modal
✓ 4.2 Crear JavaScript controller
✓ 4.3 Conectar al API REST /api/notifications
✓ 4.4 Implementar filtros
✓ 4.5 Implementar paginación
✓ 4.6 Implementar marcar como leída
✓ 4.7 Testing de carga de notificaciones
✓ 4.8 Testing de filtros
✓ 4.9 Testing de paginación
```

---

### 5. Notification Preferences Modal

**Archivo Nuevo:** inventario-retail/web_dashboard/templates/notification_preferences_modal.html

**Funcionalidad:**
- Toggle email/SMS/push notifications
- Toggle para tipos específicos (stock, order, system)
- Quiet hours (horario sin notificaciones)
- Save preferences

**HTML Structure:**

```html
<!-- Notification Preferences Modal -->
<div id="notification-preferences-modal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 10000;">
    <div style="background: white; border-radius: 8px; max-width: 500px; margin: auto; margin-top: 10vh;">
        
        <!-- Header -->
        <div style="padding: 20px; border-bottom: 1px solid #e5e7eb;">
            <h2 style="margin: 0; font-size: 18px;">Preferencias de Notificaciones</h2>
        </div>
        
        <!-- Content -->
        <div style="padding: 20px;">
            
            <!-- Channels -->
            <div style="margin-bottom: 24px;">
                <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">Canales</h3>
                
                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <input type="checkbox" id="pref-email" />
                    <span>Email</span>
                </label>
                
                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <input type="checkbox" id="pref-sms" />
                    <span>SMS</span>
                </label>
                
                <label style="display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" id="pref-push" />
                    <span>Push (In-app)</span>
                </label>
            </div>
            
            <!-- Alert Types -->
            <div style="margin-bottom: 24px;">
                <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">Tipos de Alertas</h3>
                
                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <input type="checkbox" id="pref-stock-alerts" />
                    <span>Alertas de Stock</span>
                </label>
                
                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <input type="checkbox" id="pref-order-alerts" />
                    <span>Alertas de Órdenes</span>
                </label>
                
                <label style="display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" id="pref-system-alerts" />
                    <span>Alertas del Sistema</span>
                </label>
            </div>
            
            <!-- Quiet Hours -->
            <div style="margin-bottom: 24px;">
                <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">Horario Silencioso</h3>
                <p style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">No recibir notificaciones entre</p>
                
                <div style="display: flex; gap: 8px; align-items: center;">
                    <input type="time" id="pref-quiet-start" style="padding: 6px; border: 1px solid #d1d5db; border-radius: 4px;" />
                    <span>y</span>
                    <input type="time" id="pref-quiet-end" style="padding: 6px; border: 1px solid #d1d5db; border-radius: 4px;" />
                </div>
            </div>
            
        </div>
        
        <!-- Footer -->
        <div style="padding: 16px 20px; border-top: 1px solid #e5e7eb; display: flex; gap: 8px;">
            <button onclick="closePreferencesModal()" style="flex: 1; padding: 10px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer;">Cancelar</button>
            <button onclick="savePreferences()" style="flex: 1; padding: 10px; border: none; border-radius: 4px; background: #2563eb; color: white; cursor: pointer; font-weight: 600;">Guardar</button>
        </div>
        
    </div>
</div>
```

**JavaScript Controller:**

```javascript
class NotificationPreferencesModal {
    constructor(notificationManager) {
        this.manager = notificationManager;
    }
    
    async load() {
        const response = await fetch(
            `/api/notifications/preferences/${this.manager.userId}`,
            {headers: {'X-API-Key': this.manager.apiKey}}
        );
        
        const prefs = await response.json();
        
        // Llenar formulario
        document.getElementById('pref-email').checked = prefs.email_enabled;
        document.getElementById('pref-sms').checked = prefs.sms_enabled;
        document.getElementById('pref-push').checked = prefs.push_enabled;
        document.getElementById('pref-stock-alerts').checked = prefs.stock_alerts;
        document.getElementById('pref-order-alerts').checked = prefs.order_alerts;
        document.getElementById('pref-system-alerts').checked = prefs.system_alerts;
        document.getElementById('pref-quiet-start').value = prefs.quiet_hours_start || '';
        document.getElementById('pref-quiet-end').value = prefs.quiet_hours_end || '';
    }
    
    async save() {
        const prefs = {
            email_enabled: document.getElementById('pref-email').checked,
            sms_enabled: document.getElementById('pref-sms').checked,
            push_enabled: document.getElementById('pref-push').checked,
            stock_alerts: document.getElementById('pref-stock-alerts').checked,
            order_alerts: document.getElementById('pref-order-alerts').checked,
            system_alerts: document.getElementById('pref-system-alerts').checked,
            quiet_hours_start: document.getElementById('pref-quiet-start').value,
            quiet_hours_end: document.getElementById('pref-quiet-end').value
        };
        
        await fetch(
            `/api/notifications/preferences/${this.manager.userId}`,
            {
                method: 'POST',
                headers: {
                    'X-API-Key': this.manager.apiKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(prefs)
            }
        );
        
        this.close();
    }
    
    show() {
        document.getElementById('notification-preferences-modal').style.display = 'flex';
        this.load();
    }
    
    close() {
        document.getElementById('notification-preferences-modal').style.display = 'none';
    }
}
```

**Tareas:**

```
✓ 5.1 Crear HTML del modal de preferencias
✓ 5.2 Crear JavaScript controller
✓ 5.3 Conectar al API GET /api/notifications/preferences/{user_id}
✓ 5.4 Implementar save del API POST
✓ 5.5 Agregar botón en notification center
✓ 5.6 Testing de carga de preferencias
✓ 5.7 Testing de guardado de preferencias
```

---

### 6. Notification History View (Opcional)

**Funcionalidad:**
- Historial de últimas 50 notificaciones
- Export como CSV
- Filtros avanzados

**Tareas:**

```
✓ 6.1 Crear vista de historial
✓ 6.2 Agregar paginación
✓ 6.3 Agregar búsqueda
✓ 6.4 Agregar export CSV
```

---

## 🧪 Test Plan para SEMANA 2.3

### Unit Tests (5-7 tests)

```python
✓ test_notification_center_loads_notifications
✓ test_notification_center_filters_by_status
✓ test_notification_center_pagination
✓ test_notification_center_mark_as_read
✓ test_preferences_modal_loads
✓ test_preferences_modal_saves
✓ test_preferences_modal_validation
```

### Integration Tests (5-7 tests)

```python
✓ test_websocket_to_ui_notification_flow
✓ test_websocket_to_bell_icon_counter_update
✓ test_websocket_to_toast_display
✓ test_rest_api_to_notification_center
✓ test_rest_api_to_preferences_modal
✓ test_multi_tab_sync_via_websocket
✓ test_reconnection_recovery
```

### E2E Tests (3-5 tests)

```python
✓ test_complete_notification_flow_websocket_to_ui
✓ test_mark_notification_read_from_center
✓ test_preferences_change_affects_delivery
✓ test_concurrent_notifications_multiple_users
✓ test_mobile_ui_responsive
```

### Performance Tests (2-3 tests)

```python
✓ test_ui_update_latency_< 200ms
✓ test_notification_center_load_time_< 500ms
✓ test_100_notifications_rendering_performance
```

---

## 📝 Implementation Checklist

### Phase 1: Basic Integration (1 hour)

- [ ] Include websocket-notifications.js in base.html
- [ ] Initialize WebSocket manager
- [ ] Verify connection to /ws/notifications endpoint
- [ ] Test toast notifications appear

### Phase 2: Bell Icon (30 minutes)

- [ ] Add bell icon HTML to navbar
- [ ] Update counter from WebSocket
- [ ] Add click handler to show notification center
- [ ] Style for mobile responsive

### Phase 3: Notification Center (1 hour)

- [ ] Create notification center modal
- [ ] Load notifications from REST API
- [ ] Implement pagination
- [ ] Implement filters (all/unread/read)
- [ ] Implement mark as read
- [ ] Test all functionality

### Phase 4: Preferences Modal (45 minutes)

- [ ] Create preferences modal
- [ ] Load user preferences
- [ ] Implement save functionality
- [ ] Add link from notification center
- [ ] Test all settings

### Phase 5: Testing & Polish (30 minutes)

- [ ] Run full test suite (20-30 tests)
- [ ] Fix any bugs
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] Mobile responsive testing

---

## 🚀 Success Criteria

- ✅ 20-30 tests passing (all new + no regressions)
- ✅ WebSocket connected on page load
- ✅ Toast appears in <200ms after notification
- ✅ Bell icon counter updates in real-time
- ✅ Notification center loads full list
- ✅ Mark as read works bidirectionally
- ✅ Preferences save and persist
- ✅ No JavaScript errors in console
- ✅ Works on mobile (320px+)
- ✅ No performance regressions

---

## 📚 Related Documentation

- SEMANA_2_1_NOTIFICATION_REPORT.md - Backend notification service
- SEMANA_2_2_WEBSOCKET_REPORT.md - WebSocket implementation
- dashboard_app.py - FastAPI endpoints
- websocket-notifications.js - Client-side WebSocket manager

---

## 🎯 Next Phase After SEMANA 2.3

**SEMANA 3: Dashboard Modular** (25 hours estimated)
- Drag-and-drop widget layout
- Customizable dashboard widgets
- Save/load layout per user
- Widget resize capability

**SEMANA 4: PWA Mobile + Excel** (30 hours estimated)
- Progressive Web App
- Offline mode with service workers
- Excel export functionality
- Mobile app shell
