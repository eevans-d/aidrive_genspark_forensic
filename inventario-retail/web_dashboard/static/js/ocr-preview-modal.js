/**
 * OCR Preview Modal Logic
 * ========================
 * Gestiona la interacción con el modal de preview OCR
 * - Mostrar/ocultar modal
 * - Poblar datos OCR
 * - Edición de campos
 * - Validación
 * - Envío al backend
 */

class OCRPreviewModal {
    constructor() {
        this.modal = document.getElementById('ocr-preview-modal');
        this.inlineEditModal = document.getElementById('inline-edit-modal');
        this.currentEditField = null;
        this.ocrData = null;
        this.requestId = null;
        this.editable = {};
        
        // Inicializar listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Cerrar modal con ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
        
        // Confirmar edición inline con ENTER
        const inlineInput = document.getElementById('inline-edit-input');
        if (inlineInput) {
            inlineInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.confirmInlineEdit();
                }
            });
        }
    }
    
    /**
     * Mostrar modal con datos OCR
     */
    showModal(ocrData) {
        this.ocrData = ocrData;
        this.requestId = ocrData.request_id || 'N/A';
        
        // Poblar datos
        this.populateConfidenceBadge(ocrData.confidence);
        this.populateFields(ocrData);
        this.populateItemsDetail(ocrData.items || []);
        this.populateWarnings(ocrData.warnings || []);
        this.populateSuggestions(ocrData.suggestions || []);
        
        // Mostrar modal
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Analytics
        this.logEvent('ocr_preview_shown', {
            confidence: ocrData.confidence,
            items_count: ocrData.items?.length || 0
        });
    }
    
    /**
     * Cerrar modal
     */
    closeModal() {
        this.modal.style.display = 'none';
        this.inlineEditModal.style.display = 'none';
        document.body.style.overflow = 'auto';
        this.currentEditField = null;
        this.editable = {};
    }
    
    /**
     * Poblar badge de confianza
     */
    populateConfidenceBadge(confidence) {
        const badge = document.getElementById('confidence-badge');
        const bar = document.getElementById('confidence-bar');
        const value = document.getElementById('confidence-value');
        
        // Determinar clase según confianza
        bar.className = 'confidence-bar';
        if (confidence < 80) {
            bar.classList.add('low');
        } else if (confidence < 90) {
            bar.classList.add('medium');
        } else {
            bar.classList.add('high');
        }
        
        // Animar barra
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = confidence + '%';
        }, 100);
        
        value.textContent = confidence.toFixed(1) + '%';
        
        // Color de badge dinámico
        if (confidence < 80) {
            badge.style.borderLeftColor = '#ef4444';
        } else if (confidence < 90) {
            badge.style.borderLeftColor = '#f59e0b';
        } else {
            badge.style.borderLeftColor = '#10b981';
        }
    }
    
    /**
     * Poblar campos de preview
     */
    populateFields(ocrData) {
        const fields = ['proveedor', 'fecha', 'total', 'items_count'];
        
        fields.forEach(fieldName => {
            const input = document.getElementById(`field-${fieldName}`);
            const confSpan = document.getElementById(`conf-${fieldName}`);
            
            if (input) {
                const value = ocrData[fieldName] || '';
                const confidence = ocrData[`${fieldName}_confidence`] || 0;
                
                input.value = value;
                this.editable[fieldName] = false;
                
                // Mostrar confianza individual
                if (confSpan) {
                    confSpan.textContent = `(${confidence.toFixed(0)}%)`;
                    confSpan.style.color = confidence < 80 ? '#ef4444' : confidence < 90 ? '#f59e0b' : '#10b981';
                }
            }
        });
        
        // Mostrar request ID
        document.getElementById('ocr-request-id').textContent = this.requestId;
    }
    
    /**
     * Poblar detalles de items
     */
    populateItemsDetail(items) {
        const section = document.getElementById('items-detail-section');
        const list = document.getElementById('items-detail-list');
        
        if (items.length === 0) {
            section.style.display = 'none';
            document.getElementById('field-items-count').value = '0';
            return;
        }
        
        // Mostrar sección
        section.style.display = 'block';
        document.getElementById('field-items-count').value = items.length;
        
        // Limpiar lista
        list.innerHTML = '';
        
        // Generar items
        items.forEach((item, idx) => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'item-entry';
            itemDiv.innerHTML = `
                <div class="item-entry-name">
                    ${idx + 1}. ${item.name || 'Producto'} ${item.confidence ? `(${item.confidence.toFixed(0)}%)` : ''}
                </div>
                <div class="item-entry-details">
                    <span>Cantidad: ${item.quantity || 0}</span>
                    <span>Precio: $${parseFloat(item.price || 0).toFixed(2)}</span>
                </div>
            `;
            list.appendChild(itemDiv);
        });
    }
    
    /**
     * Poblar warnings
     */
    populateWarnings(warnings) {
        const section = document.getElementById('ocr-warnings-section');
        const list = document.getElementById('ocr-warnings-list');
        
        if (warnings.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        list.innerHTML = '';
        
        warnings.forEach(warning => {
            const li = document.createElement('li');
            li.textContent = warning;
            list.appendChild(li);
        });
    }
    
    /**
     * Poblar sugerencias
     */
    populateSuggestions(suggestions) {
        const section = document.getElementById('ocr-suggestions-section');
        const list = document.getElementById('ocr-suggestions-list');
        
        if (suggestions.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        list.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            list.appendChild(li);
        });
    }
    
    /**
     * Editar campo individual
     */
    editField(fieldName) {
        this.currentEditField = fieldName;
        
        const input = document.getElementById(`field-${fieldName}`);
        const currentValue = input.value;
        
        // Mostrar modal inline
        document.getElementById('inline-edit-title').textContent = `Editar ${this.getFieldLabel(fieldName)}`;
        document.getElementById('inline-edit-input').value = currentValue;
        document.getElementById('inline-edit-input').focus();
        
        this.inlineEditModal.style.display = 'block';
        
        // Seleccionar todo el texto
        setTimeout(() => {
            document.getElementById('inline-edit-input').select();
        }, 100);
    }
    
    /**
     * Cancelar edición inline
     */
    cancelInlineEdit() {
        this.inlineEditModal.style.display = 'none';
        this.currentEditField = null;
    }
    
    /**
     * Confirmar edición inline
     */
    confirmInlineEdit() {
        if (!this.currentEditField) return;
        
        const newValue = document.getElementById('inline-edit-input').value.trim();
        const input = document.getElementById(`field-${this.currentEditField}`);
        
        if (newValue === '') {
            alert('El valor no puede estar vacío');
            return;
        }
        
        // Validar según tipo de campo
        if (!this.validateField(this.currentEditField, newValue)) {
            alert('Valor inválido para este campo');
            return;
        }
        
        // Actualizar
        input.value = newValue;
        this.editable[this.currentEditField] = true;
        
        // Resaltar campo como editado
        input.style.backgroundColor = '#fef3c7';
        setTimeout(() => {
            input.style.backgroundColor = '#f9fafb';
        }, 500);
        
        // Cerrar modal inline
        this.cancelInlineEdit();
        
        // Log
        this.logEvent('ocr_field_edited', {
            field: this.currentEditField,
            was_edited: true
        });
    }
    
    /**
     * Validar campo
     */
    validateField(fieldName, value) {
        switch (fieldName) {
            case 'fecha':
                // Validar formato YYYY-MM-DD
                return /^\d{4}-\d{2}-\d{2}$/.test(value);
            
            case 'total':
                // Validar número positivo
                const num = parseFloat(value);
                return !isNaN(num) && num > 0;
            
            case 'proveedor':
            case 'items_count':
                return value.length > 0;
            
            default:
                return true;
        }
    }
    
    /**
     * Obtener etiqueta amigable del campo
     */
    getFieldLabel(fieldName) {
        const labels = {
            'proveedor': 'Proveedor',
            'fecha': 'Fecha',
            'total': 'Total',
            'items_count': 'Cantidad de Items'
        };
        return labels[fieldName] || fieldName;
    }
    
    /**
     * Editar todos los campos
     */
    editAllFields() {
        const fields = ['proveedor', 'fecha', 'total', 'items_count'];
        fields.forEach(fieldName => {
            const input = document.getElementById(`field-${fieldName}`);
            if (input) {
                input.removeAttribute('readonly');
                input.style.backgroundColor = '#fff8dc';
            }
        });
        
        // Cambiar botón
        const btn = document.getElementById('confirm-ocr-btn');
        btn.textContent = '✅ Confirmar Cambios';
        
        this.logEvent('ocr_edit_all_enabled');
    }
    
    /**
     * Mostrar/ocultar detalles de items
     */
    toggleItemsDetail() {
        const section = document.getElementById('items-detail-section');
        if (section.style.display === 'none') {
            section.style.display = 'block';
            this.logEvent('ocr_items_expanded');
        } else {
            section.style.display = 'none';
            this.logEvent('ocr_items_collapsed');
        }
    }
    
    /**
     * Confirmar y procesar OCR
     */
    async confirmOCR() {
        // Validar campos editables
        if (!this.validateAllFields()) {
            alert('Por favor, revisa los campos inválidos');
            return;
        }
        
        // Recolectar datos finales
        const finalData = {
            request_id: this.requestId,
            proveedor: document.getElementById('field-proveedor').value,
            fecha: document.getElementById('field-fecha').value,
            total: parseFloat(document.getElementById('field-total').value),
            items_count: parseInt(document.getElementById('field-items-count').value),
            confidence: this.ocrData.confidence,
            items: this.ocrData.items || [],
            edited_fields: Object.keys(this.editable).filter(k => this.editable[k])
        };
        
        // Deshabilitar botón
        const btn = document.getElementById('confirm-ocr-btn');
        btn.disabled = true;
        btn.innerHTML = '⏳ Procesando...';
        
        try {
            // Enviar al backend
            const response = await fetch('/api/ocr/confirm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.getAPIKey()
                },
                body: JSON.stringify(finalData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            // Mostrar éxito
            alert('✅ Factura procesada correctamente');
            
            // Disparar evento personalizado
            window.dispatchEvent(new CustomEvent('ocr-confirmed', {
                detail: result
            }));
            
            // Log
            this.logEvent('ocr_confirmed', {
                confidence: finalData.confidence,
                edited_fields: finalData.edited_fields.length
            });
            
            // Cerrar modal
            this.closeModal();
            
        } catch (error) {
            console.error('Error confirmando OCR:', error);
            alert('❌ Error al procesar la factura. Intenta nuevamente.');
            
            this.logEvent('ocr_confirmation_error', {
                error: error.message
            });
            
        } finally {
            btn.disabled = false;
            btn.innerHTML = '✅ Confirmar y Procesar';
        }
    }
    
    /**
     * Validar todos los campos
     */
    validateAllFields() {
        const validations = [
            ['proveedor', document.getElementById('field-proveedor').value],
            ['fecha', document.getElementById('field-fecha').value],
            ['total', document.getElementById('field-total').value]
        ];
        
        for (const [field, value] of validations) {
            if (!this.validateField(field, value)) {
                console.warn(`Validación fallida: ${field} = ${value}`);
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Obtener API Key
     */
    getAPIKey() {
        // Obtener del localStorage o del meta tag
        return localStorage.getItem('api_key') || 
               document.querySelector('meta[name="api-key"]')?.content || 
               'dev';
    }
    
    /**
     * Logging para analytics
     */
    logEvent(eventName, data = {}) {
        console.log(`[OCR Event] ${eventName}`, data);
        
        // Aquí se puede integrar con analytics
        if (window.gtag) {
            gtag('event', eventName, data);
        }
    }
}

// ============================================
// Funciones Globales para HTML
// ============================================

let ocrPreviewModal = null;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    ocrPreviewModal = new OCRPreviewModal();
});

/**
 * Mostrar modal OCR desde cualquier lado
 */
function showOCRPreview(ocrData) {
    if (!ocrPreviewModal) {
        ocrPreviewModal = new OCRPreviewModal();
    }
    ocrPreviewModal.showModal(ocrData);
}

/**
 * Cerrar modal OCR
 */
function closeOCRPreview() {
    if (ocrPreviewModal) {
        ocrPreviewModal.closeModal();
    }
}

/**
 * Editar campo OCR
 */
function editField(fieldName) {
    if (ocrPreviewModal) {
        ocrPreviewModal.editField(fieldName);
    }
}

/**
 * Cancelar edición inline
 */
function cancelInlineEdit() {
    if (ocrPreviewModal) {
        ocrPreviewModal.cancelInlineEdit();
    }
}

/**
 * Confirmar edición inline
 */
function confirmInlineEdit() {
    if (ocrPreviewModal) {
        ocrPreviewModal.confirmInlineEdit();
    }
}

/**
 * Editar todos los campos
 */
function editAllFields() {
    if (ocrPreviewModal) {
        ocrPreviewModal.editAllFields();
    }
}

/**
 * Toggle detalles de items
 */
function toggleItemsDetail() {
    if (ocrPreviewModal) {
        ocrPreviewModal.toggleItemsDetail();
    }
}

/**
 * Confirmar OCR
 */
function confirmOCR() {
    if (ocrPreviewModal) {
        ocrPreviewModal.confirmOCR();
    }
}
